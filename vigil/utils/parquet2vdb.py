# https://github.com/deadbits/vigil-llm
import os
import sys
import argparse
import logging
import pandas as pd

import chromadb

from uuid import uuid4

from chromadb.config import Settings
from chromadb.utils import embedding_functions

from vigil.config import Config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDB:
    def __init__(self, config_dict: dict):
        self.name = 'database:vector'
        if config_dict['embed_fn'] == 'openai':
            self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=config_dict['openai_key'],
                model_name=config_dict['openai_model']
            )
        else:
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=config_dict['embed_fn']
            )

        self.db_dir = config_dict['db_dir']
        self.n_results = int(config_dict['n_results'])
        self.collection_name = config_dict['collection_name']

        self.client = chromadb.PersistentClient(
            path=self.db_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.get_or_create_collection(self.collection_name)
        logger.info(f'[{self.name}] initialized database')

    def get_or_create_collection(self, name):
        logger.info(f'[{self.name}] Using collection: {name}')
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embed_fn,
        )
        return self.collection

    def add_texts(self, texts: list, ids: list):
        logger.info(f'[{self.name}] Adding {len(texts)} to database')
        try:
            self.collection.add(
                documents=texts,
                ids=ids
            )
        except Exception as err:
            logger.error(f'[{self.name}] Failed to add texts to collection: {err}')


def process_file(fpath, chunk_size=100):
    texts = []
    ids = []

    df = pd.read_parquet(fpath)

    for idx, entry in df.iterrows():
        text = entry.get('text', None)

        if text:
            unique_id = str(uuid4())
            texts.append(text)
            ids.append(unique_id)

        if (idx + 1) % chunk_size == 0:
            if texts and ids:
                vdb.add_texts(texts, ids)
            texts = []
            ids = []

    if texts and ids:
        vdb.add_texts(texts, ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load text embedding data into VectorDB from JSON files.")

    parser.add_argument(
        '-d', '--directory', 
        help='directory containing JSON files',
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

    args = parser.parse_args()
    directory = args.directory

    # vector db scanner config
    vdb_dir = conf.get_val('vectordb', 'db_dir')
    vdb_collection = conf.get_val('vectordb', 'collection_name')
    vdb_n_results = conf.get_val('vectordb', 'n_results')

    if not os.path.isdir(vdb_dir):
        logger.error(f'[main] VectorDB directory not found: {vdb_dir}')
        sys.exit(1)

    # text embedding model
    emb_model = conf.get_val('embedding', 'model')
    if emb_model is None:
        logger.warn('[main] No embedding model set in config file')
        sys.exit(1)

    if emb_model == 'openai':
        logger.info('[main] Using OpenAI embedding model')
        openai_key = conf.get_val('embedding', 'openai_api_key')
        openai_model = conf.get_val('embedding', 'openai_model')

        if openai_key is None or openai_model is None:
            logger.error('[main] OpenAI embedding model selected but no key or model name set in config')
            sys.exit(1)

        vdb = VectorDB(config_dict={
            'collection_name': vdb_collection,
            'embed_fn': 'openai',
            'openai_key': openai_key,
            'openai_model': openai_model,
            'db_dir': vdb_dir,
            'n_results': vdb_n_results
        })

    else:
        logger.info('[main] Using SentenceTransformer embedding model')   

        vdb = VectorDB(config_dict={
            'collection_name': vdb_collection,
            'embed_fn': emb_model,
            'db_dir': vdb_dir,
            'n_results': vdb_n_results
        })
    for filename in os.listdir(directory):
        if filename.endswith(".parquet"):  # <-- Look for .parquet files
            filepath = os.path.join(directory, filename)
            print(f"Processing {filepath}...")
            process_file(filepath)
