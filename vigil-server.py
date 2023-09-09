# https://github.com/deadbits/vigil-llm
import os
import sys
import argparse
import logging

from collections import OrderedDict
from flask import Flask, request, jsonify, abort

from vigil.config import Config

from vigil.scanners.yara import YaraScanner
from vigil.scanners.vectordb import VectorScanner
from vigil.scanners.transformer import TransformerScanner

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


@app.route('/settings', methods=['GET'])
def show_settings():
    logger.info(f'[{log_name}] ({request.path}) Returning config dictionary')
    config_dict = {s:dict(conf.config.items(s)) for s in conf.config.sections()}

    if 'embedding' in config_dict:
        config_dict['embedding'].pop('openai_api_key', None)

    return jsonify(config_dict)


@app.route('/analyze', methods=['POST'])
def analyze_prompt():
    input_prompt = request.json.get('prompt', '')
    cached_response = lru_cache.get(input_prompt)

    if cached_response:
        logger.info(f'[{log_name}] ({request.path}) Found response in cache!')
        cached_response['cached'] = True
        return jsonify(cached_response)

    if input_prompt is None:
        logger.error(f'[{log_name}] ({request.path}) Missing "prompt" field')
        abort(400, 'Missing "prompt" field')

    if not isinstance(input_prompt, str):
        logger.error(f'[{log_name}] ({request.path}) Invalid data type; "prompt" value must be a string')
        abort(400, 'Invalid data type; "prompt" value must be a string')

    result = mgr.perform_scan(input_prompt)

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

    input_scanners = conf.get_val('scanners', 'input_scanners')
    if input_scanners is None:
        logger.error(f'[{log_name}] No input scanners set in config')
        sys.exit(1)

    try:
        input_scanners = input_scanners.split(',')
    except:
        input_scanners = [input_scanners]

    use_scanners = []

    for name in input_scanners:

        # Transformer scanner config
        if name == 'transformer':
            lm_name = conf.get_val('scanner:transformer', 'model')
            if lm_name is None:
                logger.error(f'[{log_name}] No model name for model scanner set in config')
                sys.exit(1)

            threshold = conf.get_val('scanner:transformer', 'threshold')
            if threshold is None:
                logger.error(f'[{log_name}] No threshold for model scanner set in config')
                sys.exit(1)

            lm_scanner = TransformerScanner(config_dict={
                'model': lm_name,
                'threshold': threshold
            })

            use_scanners.append(lm_scanner)

        # YARA scanner config
        elif name == 'yara':
            yara_dir = conf.get_val('scanner:yara', 'rules_dir')
            if yara_dir is None:
                logger.error(f'[{log_name}] No yara rules directory set in config')
                sys.exit(1)

            yara_scanner = YaraScanner(config_dict={'rules_dir': yara_dir})
            yara_scanner.load_rules()
            use_scanners.append(yara_scanner)

        # vector db scanner config
        elif name == 'vectordb':
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
                logger.warn(f'[{log_name}] No embedding model set in config file')
                sys.exit(1)

            if emb_model == 'openai':
                logger.info(f'[{log_name}] Using OpenAI embedding model')
                openai_key = conf.get_val('embedding', 'openai_api_key')
                openai_model = conf.get_val('embedding', 'openai_model')

                if openai_key is None or openai_model is None:
                    logger.error(f'[{log_name}] OpenAI embedding model selected but no key or model name set in config')
                    sys.exit(1)

                vector_scanner = VectorScanner(config_dict={
                    'collection_name': vdb_collection,
                    'embed_fn': 'openai',
                    'openai_key': openai_key,
                    'openai_model': openai_model,
                    'threshold': vdb_threshold,
                    'db_dir': vdb_dir,
                    'n_results': vdb_n_results
                })

            else:
                logger.info(f'[{log_name}] Using SentenceTransformer embedding model')

                vector_scanner = VectorScanner(config_dict={
                    'collection_name': vdb_collection,
                    'embed_fn': emb_model,
                    'threshold': vdb_threshold,
                    'db_dir': vdb_dir,
                    'n_results': vdb_n_results
                })

            use_scanners.append(vector_scanner)

        else:
            logger.warning(f'[{log_name}] Unsupported scanner set in config: {name}')

    mgr = Manager(scanners=use_scanners)

    lru_cache = LRUCache(capacity=100)

    app.run(debug=True)
