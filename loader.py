import os
import sys
import json
import argparse

from datasets import load_dataset

from loguru import logger

from vigil.core.config import Config
from vigil.core.vectordb import VectorDB


class Loader:
    def __init__(self, vector_db, chunk_size=100):
        self.vector_db = vector_db
        self.chunk_size = chunk_size

    def load_dataset(self, dataset_name: str):
        buffer = []

        logger.info(f'Loading dataset: {dataset_name}')
        try:
            docs_stream = load_dataset(
                dataset_name,
                split='train',
                streaming=True)
        except Exception as err:
            logger.error(f'Error loading dataset: {err}')
            raise

        logger.info('Reading dataset stream ...')

        for doc in docs_stream:
            buffer.append({
                'text': doc['text'],
                'embeddings': doc['embeddings'],
                'metadata': {'model': doc['model']}
            })
            if len(buffer) >= self.chunk_size:
                self.process_chunk(buffer)
                buffer.clear()

        if buffer:
            self.process_chunk(buffer)
        
        logger.info('Finished loading dataset.')

    def process_chunk(self, chunk):
        texts = [doc['text'] for doc in chunk]
        embeddings = [doc['embeddings'] for doc in chunk]
        metadatas = [doc['metadata'] for doc in chunk]
        self.vector_db.add_embeddings(texts, embeddings, metadatas)
        logger.info(f'Processed chunk; {len(chunk)}')


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

    # read vectordb config
    vdb_dir = conf.get_val('scanner:vectordb', 'db_dir')
    vdb_collection = conf.get_val('scanner:vectordb', 'collection')
    n_results = conf.get_val('scanner:vectordb', 'n_results')

    logger.info(f'using database directory: {vdb_dir}')

    if not os.path.isdir(vdb_dir):
        logger.error(f'VectorDB directory not found: {vdb_dir}')
        sys.exit(1)

    # text embedding model
    emb_model = conf.get_val('embedding', 'model')
    if emb_model is None:
        logger.warn('No embedding model set in config file')
        sys.exit(1)

    if emb_model == 'openai':
        openai_key = conf.get_val('embedding', 'openai_api_key')
        openai_model = conf.get_val('embedding', 'openai_model')

        if openai_key is None or openai_model is None:
            logger.error('OpenAI embedding model selected but no key or model name set in config')
            sys.exit(1)

        vdb = VectorDB(config_dict={
            'collection_name': vdb_collection,
            'embed_fn': 'openai',
            'openai_key': openai_key,
            'openai_model': openai_model,
            'db_dir': vdb_dir,
            'n_results': n_results
        })

    else:
        vdb = VectorDB(config_dict={
            'collection_name': vdb_collection,
            'embed_fn': emb_model,
            'db_dir': vdb_dir,
            'n_results': n_results
        })

    data_loader = Loader(vector_db=vdb)
    data_loader.load_dataset(args.dataset)
