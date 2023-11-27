import os
import sys
import argparse

from loguru import logger

from vigil.core.config import Config
from vigil.core.loader import Loader

from vigil.core.vectordb import VectorDB


def setup_vectordb(conf: Config) -> VectorDB:
    full_config = conf.get_general_config()
    params = full_config.get('vectordb', {})
    params.update(full_config.get('embedding', {}))
    return VectorDB(**params)


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
    vdb = setup_vectordb(conf)

    data_loader = Loader(vector_db=vdb)
    data_loader.load_dataset(args.dataset)
