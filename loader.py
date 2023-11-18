import os
import sys
import argparse

from loguru import logger

from vigil.core.config import Config
from vigil.core.loader import Loader

from vigil.vigil import setup_vectordb


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Load text embedding data into Vigil'
    )

    parser.add_argument(
        '-d', '--dataset',
        help='dataset repo name',
        type=str,
        required=True
    )

    parser.add_argument(
        '-c', '--config',
        help='config file',
        type=str,
        required=True
    )

    args = parser.parse_args()

    conf = Config(args.config)

    embedding_conf = conf.get_general_config().get('embedding', {})
    scanner_conf = conf.get_scanner_config('vectordb')

    logger.info(f'using database directory: {scanner_conf.get("db_dir")}')
    vdb = setup_vectordb(scanner_conf, embedding_conf)

    data_loader = Loader(vector_db=vdb)
    data_loader.load_dataset(args.dataset)
