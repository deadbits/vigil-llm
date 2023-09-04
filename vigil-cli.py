# https://github.com/deadbits/vigil-llm
import os
import sys
import json
import argparse
import logging

from vigil.config import Config

from vigil.scanners.yara import YaraScanner
from vigil.scanners.transformer import TransformerScanner
from vigil.scanners.vectordb import VectorScanner

from vigil.dispatch import Manager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

log_name = 'cli:main'


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
        required=True,
        help='The prompt text to analyze'
    )

    args = parser.parse_args()

    conf = Config(args.config)

    input_scanners = conf.get_val('scanners', 'input_scanners')
    if input_scanners is None:
        logger.error('[{log_name}] No input scanners set in config')
        sys.exit(1)

    try:
        input_scanners = input_scanners.split(',')
    except Exception as err:
        input_scanners = [input_scanners]

    use_scanners = []

    for name in input_scanners:
        if name == 'transformer':
            # Transformer scanner config
            lm_name = conf.get_val('scanner:transformer', 'model')
            if lm_name is None:
                logger.error('[{log_name}] No model name for model scanner set in config')
                sys.exit(1)

            threshold = conf.get_val('scanner:transformer', 'threshold')
            if threshold is None:
                logger.error('[{log_name}] No threshold for model scanner set in config')
                sys.exit(1)

            lm_scanner = TransformerScanner(config_dict={
                'model': lm_name,
                'threshold': threshold
            })

            use_scanners.append(lm_scanner)

        elif name == 'yara':
            # YARA scanner config
            yara_dir = conf.get_val('scanner:yara', 'rules_dir')
            if yara_dir is None:
                logger.error('[{log_name}] No yara rules directory set in config')
                sys.exit(1)

            yara_scanner = YaraScanner(config_dict={'rules_dir': yara_dir})
            yara_scanner.load_rules()
            use_scanners.append(yara_scanner)

        elif name == 'vectordb':
            # vector db scanner config
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
                logger.warn('[{log_name}] No embedding model set in config file')
                sys.exit(1)

            if emb_model == 'openai':
                logger.info('[{log_name}] Using OpenAI embedding model')
                openai_key = conf.get_val('embedding', 'openai_api_key')
                openai_model = conf.get_val('embedding', 'openai_model')

                if openai_key is None or openai_model is None:
                    logger.error('[{log_name}] OpenAI embedding model selected but no key or model name set in config')
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
                logger.info('[{log_name}] Using SentenceTransformer embedding model')

                vector_scanner = VectorScanner(config_dict={
                    'collection_name': vdb_collection,
                    'embed_fn': emb_model,
                    'threshold': vdb_threshold,
                    'db_dir': vdb_dir,
                    'n_results': vdb_n_results
                })

            use_scanners.append(vector_scanner)

        else:
            logger.warn(f'[{log_name}] Unsupported scanner set in config: {name}')

    mgr = Manager(scanners=use_scanners)
    result = mgr.perform_scan(args.prompt)
    print(json.dumps(result, indent=4))
