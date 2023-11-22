# https://github.com/deadbits/vigil-llm
import chromadb

from loguru import logger

from typing import List, Optional

from chromadb.config import Settings
from chromadb.utils import embedding_functions

from vigil.common import uuid4_str


class VectorDB:
    def __init__(self, 
        model: str, 
        collection: str, 
        db_dir: str,
        n_results: int, 
        openai_key: Optional[str] = None
    ):
        """ Initialize Chroma vector db client """
        self.name = 'database:vector'

        if model == 'openai':
            logger.info('Using OpenAI embedding function')
            self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_key,
                model_name='text-embedding-ada-002'
            )
        else:
            logger.info(f'Using SentenceTransformer embedding function: {config_dict["embed_fn"]}')
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model
            )

        self.collection = collection
        self.db_dir = db_dir
        self.n_results = int(n_results)

        if not hasattr(self.embed_fn, "__call__"):
            logger.error('Embedding function is not callable')
            raise ValueError('Embedding function is not a function')

        self.client = chromadb.PersistentClient(
            path=self.db_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.get_or_create_collection(self.collection)
        logger.success('Loaded database')

    def get_or_create_collection(self, name: str):
        logger.info(f'Using collection: {name}')
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embed_fn,
            metadata={'hnsw:space': 'cosine'}
        )
        return self.collection

    def add_texts(self, texts: List[str], metadatas: List[dict]):
        success = False

        logger.info(f'Adding {len(texts)} texts')
        ids = [uuid4_str() for _ in range(len(texts))]

        try:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            success = True
        except Exception as err:
            logger.error(f'Failed to add texts to collection: {err}')

        return (success, ids)

    def add_embeddings(self, texts: List[str], embeddings: List[List], metadatas: List[dict]):
        success = False

        logger.info(f'Adding {len(texts)} embeddings')
        ids = [uuid4_str() for _ in range(len(texts))]

        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            success = True
        except Exception as err:
            logger.error(f'Failed to add texts to collection: {err}')

        return (success, ids)

    def query(self, text: str):
        logger.info(f'Querying database for: {text}')
        try:
            return self.collection.query(
                query_texts=[text],
                n_results=self.n_results)
        except Exception as err:
            logger.error(f'Failed to query database: {err}')
