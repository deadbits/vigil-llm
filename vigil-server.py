# https://github.com/deadbits/vigil-llm
import os
import sys
import argparse
import logging

from collections import OrderedDict
from flask import Flask, request, jsonify, abort

from vigil.config import Config

# from vigil.scanners.yara import YaraScanner
from vigil.scanners.vectordb import VectorScanner
from vigil.scanners.transformer import TransformerScanner
from vigil.scanners.similarity import SimilarityScanner

from vigil.dispatch import Manager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

log_name = 'server:main'


class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str):
        if key in self.cache:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None

    def set(self, key: str, value: any):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value


def setup_yara_scanner(conf):
    yara_dir = conf.get_val('scanner:yara', 'rules_dir')
    if yara_dir is None:
        logger.error(f'[{log_name}] No yara rules directory set in config')
        sys.exit(1)

    #yara_scanner = YaraScanner(config_dict={'rules_dir': yara_dir})
    #yara_scanner.load_rules()
    #return yara_scanner


def setup_vectordb_scanner(conf):
    vdb_dir = conf.get_val('scanner:vectordb', 'db_dir')
    vdb_collection = conf.get_val('scanner:vectordb', 'collection')
    vdb_threshold = conf.get_val('scanner:vectordb', 'threshold')
    vdb_n_results = conf.get_val('scanner:vectordb', 'n_results')

    if not os.path.isdir(vdb_dir):
        logger.error(f'[{log_name}] VectorDB directory not found: {vdb_dir}')
        sys.exit(1)

    # text embedding model
    emb_model = conf.get_val('embedding', 'model')
    if emb_model is None:
        logger.error(f'[{log_name}] No embedding model set in config file')
        sys.exit(1)

    if emb_model == 'openai':
        logger.info(f'[{log_name}] Using OpenAI embedding model')
        openai_key = conf.get_val('embedding', 'openai_api_key')

        if openai_key is None:
            logger.error(f'[{log_name}] OpenAI embedding model selected but no key or model name set in config')
            sys.exit(1)

    return VectorScanner(config_dict={
        'collection_name': vdb_collection,
        'embed_fn': emb_model,
        'openai_key': openai_key if openai_key else None,
        'threshold': vdb_threshold,
        'db_dir': vdb_dir,
        'n_results': vdb_n_results
    })


def setup_similarity_scanner(conf):
    sim_threshold = conf.get_val('scanner:similarity', 'threshold')
    emb_model = conf.get_val('embedding', 'model')

    if not sim_threshold or not emb_model:
        logger.error(f'[{log_name}] Missing configurations for Similarity Scanner')
        sys.exit(1)

    if emb_model == 'openai':
        openai_key = conf.get_val('embedding', 'openai_api_key')

    return SimilarityScanner(config_dict={
        'threshold': sim_threshold,
        'model_name': emb_model,
        'openai_key': openai_key if openai_key else None
    })


def setup_transformer_scanner(conf):
    lm_name = conf.get_val('scanner:transformer', 'model')
    threshold = conf.get_val('scanner:transformer', 'threshold')

    if not lm_name or not threshold:
        logger.error(f'[{log_name}] Missing configurations for Transformer Scanner')
        sys.exit(1)

    return TransformerScanner(config_dict={
        'model': lm_name,
        'threshold': threshold
    })


def check_field(data, field_name: str, field_type: type) -> str:
    field_data = data.get(field_name, "")

    if not field_data:
        logger.error(f'[{log_name}] ({request.path}) Missing "{field_name}" field')
        abort(400, f'Missing "{field_name}" field')

    if not isinstance(field_data, field_type):
        logger.error(f'[{log_name}] ({request.path}) Invalid data type; "{field_name}" value must be a {field_type.__name__}')
        abort(400, f'Invalid data type; "{field_name}" value must be a {field_type.__name__}')

    return field_data


@app.route('/settings', methods=['GET'])
def show_settings():
    """ Return the current configuration settings """
    logger.info(f'[{log_name}] ({request.path}) Returning config dictionary')
    config_dict = {s: dict(conf.config.items(s)) for s in conf.config.sections()}

    if 'embedding' in config_dict:
        config_dict['embedding'].pop('openai_api_key', None)

    return jsonify(config_dict)


@app.route('/analyze/response', methods=['POST'])
def analyze_response():
    """ Analyze a prompt and its response """
    logger.info(f'[{log_name}] ({request.path}) Received request')

    input_prompt = check_field(request.json, 'prompt', str)
    out_data = check_field(request.json, 'response', str)

    result = out_mgr.perform_scan(input_prompt, out_data)

    logger.info(f'[{log_name}] ({request.path}) Returning response')

    return jsonify(result)


@app.route('/analyze/prompt', methods=['POST'])
def analyze_prompt():
    """ Analyze a prompt against a set of scanners """
    logger.info(f'[{log_name}] ({request.path}) Received request')

    input_prompt = check_field(request.json, 'prompt', str)
    cached_response = lru_cache.get(input_prompt)

    if cached_response:
        logger.info(f'[{log_name}] ({request.path}) Found response in cache!')
        cached_response['cached'] = True
        return jsonify(cached_response)

    result = in_mgr.perform_scan(input_prompt)

    logger.info(f'[{log_name}] ({request.path}) Returning response')
    lru_cache.set(input_prompt, result)

    return jsonify(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config',
        help='config file',
        type=str,
        required=True
    )

    args = parser.parse_args()

    global conf
    conf = Config(args.config)

    in_scanners = conf.get_val('scanners', 'input_scanners')
    if in_scanners is None:
        logger.error(f'[{log_name}] No input scanners set in config')
        sys.exit(1)

    out_scanners = conf.get_val('scanners', 'output_scanners')
    if out_scanners is None:
        logger.warn(f'[{log_name}] No output scanners set in config; continuing')

    try:
        in_scanners = in_scanners.split(',')
    except Exception as err:
        in_scanners = [in_scanners]

    try:
        out_scanners = out_scanners.split(',')
    except Exception as err:
        out_scanners = [out_scanners]

    # i already used the good variable names :(
    inputs = []
    outputs = []

    SCANNER_SETUPS = {
        'similarity': setup_similarity_scanner,
        'transformer': setup_transformer_scanner,
        'yara': setup_yara_scanner,
        'vectordb': setup_vectordb_scanner
    }

    for name in out_scanners:
        setup_fn = SCANNER_SETUPS.get(name)
        if not setup_fn:
            logger.warning(f'[{log_name}] Unsupported scanner set in config: {name}')
            continue
        scanner = setup_fn(conf)
        outputs.append(scanner)

    for name in in_scanners:
        setup_fn = SCANNER_SETUPS.get(name)
        if not setup_fn:
            logger.warning(f'[{log_name}] Unsupported scanner set in config: {name}')
            continue
        scanner = setup_fn(conf)
        inputs.append(scanner)

    in_mgr = Manager(scanners=inputs)
    out_mgr = Manager(scanners=outputs)

    lru_cache = LRUCache(capacity=100)

    app.run(debug=True)
