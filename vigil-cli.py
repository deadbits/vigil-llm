# https://github.com/deadbits/vigil-llm
import os
import sys
import json
import argparse

from pygments import lexers
from pygments import highlight
from pygments import formatters

from loguru import logger

from vigil.config import Config

from vigil.scanners.yara import YaraScanner
from vigil.scanners.transformer import TransformerScanner
from vigil.scanners.vectordb import VectorScanner
from vigil.scanners.similarity import SimilarityScanner

from vigil.dispatch import Manager
from vigil.vectordb import VectorDB


logger.add('logs/cli.log', format="{time} {level} {message}", level="INFO")


def setup_yara_scanner(conf):
    yara_dir = conf.get_val('scanner:yara', 'rules_dir')
    if yara_dir is None:
        logger.error(f'No yara rules directory set in config')
        sys.exit(1)

    yara_scanner = YaraScanner(config_dict={'rules_dir': yara_dir})
    yara_scanner.load_rules()
    return yara_scanner


def setup_vectordb_scanner(conf):
    vdb_dir = conf.get_val('scanner:vectordb', 'db_dir')
    vdb_collection = conf.get_val('scanner:vectordb', 'collection')
    vdb_threshold = conf.get_val('scanner:vectordb', 'threshold')
    vdb_n_results = conf.get_val('scanner:vectordb', 'n_results')

    if not os.path.isdir(vdb_dir):
        logger.error(f'VectorDB directory not found: {vdb_dir}')
        sys.exit(1)

    # text embedding model
    emb_model = conf.get_val('embedding', 'model')
    if emb_model is None:
        logger.error('No embedding model set in config file')
        sys.exit(1)

    if emb_model == 'openai':
        logger.info('Using OpenAI embedding model')
        openai_key = conf.get_val('embedding', 'openai_api_key')

        if openai_key is None:
            logger.error('OpenAI embedding model selected but no key or model name set in config')
            sys.exit(1)

    global vectordb
    vectordb = VectorDB(
        config_dict={
            'db_dir': vdb_dir,
            'collection_name': vdb_collection,
            'n_results': vdb_n_results,
            'embed_fn': emb_model,
            'openai_key': openai_key if openai_key else None
        }
    )

    return VectorScanner(
        config_dict={'threshold': float(vdb_threshold)},
        db_client=vectordb
    )


def setup_similarity_scanner(conf):
    sim_threshold = conf.get_val('scanner:similarity', 'threshold')
    emb_model = conf.get_val('embedding', 'model')

    if not sim_threshold or not emb_model:
        logger.error('Missing configurations for Similarity Scanner')
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
        logger.error('Missing configurations for Transformer Scanner')
        sys.exit(1)

    return TransformerScanner(config_dict={
        'model': lm_name,
        'threshold': threshold
    })



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='vigil-cli',
        description='Analyze prompts for various threats',
        epilog='vigil-cli -c conf/sever.conf -p "prompt text"'
    )

    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Path to the config file'
    )

    parser.add_argument(
        '-p', '--prompt',
        type=str,
        required=True,
        help='The prompt text to analyze'
    )

    parser.add_argument(
        '-r', '--response',
        type=str,
        required=False,
        help='The response text to analyze'
    )

    args = parser.parse_args()

    conf = Config(args.config)

    in_scanners = conf.get_val('scanners', 'input_scanners')
    if in_scanners is None:
        logger.error('No input scanners set in config')
        sys.exit(1)

    out_scanners = conf.get_val('scanners', 'output_scanners')
    if out_scanners is None:
        logger.warn('No output scanners set in config; continuing')

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
            logger.warning(f'Unsupported scanner set in config: {name}')
            continue
        scanner = setup_fn(conf)
        outputs.append(scanner)

    for name in in_scanners:
        setup_fn = SCANNER_SETUPS.get(name)
        if not setup_fn:
            logger.warning(f'Unsupported scanner set in config: {name}')
            continue
        scanner = setup_fn(conf)
        inputs.append(scanner)

    vdb_auto_update = conf.get_bool('embedding', 'auto_update')
    vdb_update_thres = conf.get_val('embedding', 'update_threshold')

    common_args = {
        'scanners': inputs,
        'auto_update': vdb_auto_update if vdb_auto_update else False,
        'update_threshold': int(vdb_update_thres) if vdb_update_thres else 3,
        'db_client': vectordb if vdb_auto_update else None
    }

    if args.response:
        out_mgr = Manager(name='input', **common_args)
        result = out_mgr.perform_scan(input_prompt=args.response)
    else:
        mgr = Manager(name='output', **common_args)
        mgr = Manager(scanners=inputs)
        result = mgr.perform_scan(input_prompt=args.prompt)

    print(
        highlight(
            json.dumps(result, indent=2),
            lexers.JsonLexer(),
            formatters.TerminalFormatter()
        )
    )
