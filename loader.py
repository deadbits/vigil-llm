import argparse
from pathlib import Path
import sys
from loguru import logger

from vigil.core.config import ConfigFile
from vigil.core.loader import Loader
from vigil.vigil import setup_vectordb


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load text embedding data into Vigil")

    parser.add_argument(
        "-d", "--dataset", help="dataset repo name", type=str, required=False
    )

    parser.add_argument(
        "-D", "--datasets", help="Specify multiple repos", type=str, required=False
    )

    parser.add_argument("-c", "--config", help="config file", type=str, required=True)

    args = parser.parse_args()

    conf = ConfigFile.from_config_file(Path(args.config))

    vdb = setup_vectordb(conf)

    data_loader = Loader(vector_db=vdb)

    loaded_something = False

    if args.datasets:
        for dataset in args.datasets.split(","):
            data_loader.load_dataset(dataset)
            loaded_something = True
    if args.dataset:
        data_loader.load_dataset(args.dataset)
        loaded_something = True

    if not loaded_something:
        logger.error("Please specify a dataset or datasets!")
        sys.exit(1)
