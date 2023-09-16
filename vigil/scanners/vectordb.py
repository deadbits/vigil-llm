import uuid
import chromadb
import logging

from chromadb.config import Settings
from chromadb.utils import embedding_functions

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import VectorMatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:vectordb'

        if config_dict['embed_fn'] == 'openai':
            logger.info(f'[{self.name}] Using OpenAI embedding function')
            self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=config_dict['openai_key'],
                model_name='text-embedding-ada-002'
            )
        else:
            logger.info(f'[{self.name}] Using SentenceTransformer embedding function: {config_dict["embed_fn"]}')
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=config_dict['embed_fn']
            )

        self.threshold = float(config_dict['threshold'])
        self.db_dir = config_dict['db_dir']
        self.n_results = int(config_dict['n_results'])
        self.collection_name = config_dict['collection_name']

        if not hasattr(self.embed_fn, "__call__"):
            logger.error(f'[{self.name}] Embedding function is not callable')
            raise ValueError('[scanner:vectordb] Embedding function is not a function')

        self.client = chromadb.PersistentClient(
            path=self.db_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.get_or_create_collection(self.collection_name)
        logger.info(f'[{self.name}] Loaded scanner')

    def get_or_create_collection(self, name):
        logger.info(f'[{self.name}] Using collection: {name}')
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embed_fn,
            metadata={'hnsw:space': 'cosine'}
        )
        return self.collection

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'[{self.name}] Performing scan; id="{scan_id}"')

        try:
            matches = self.collection.query(
                query_texts=[scan_obj.prompt],
                n_results=self.n_results
            )
        except Exception as err:
            logger.error(f'[{self.name}] Failed to perform vector scan; id="{scan_id}" error="{err}"')
            return scan_obj

        for match in zip(matches["documents"][0], matches["metadatas"][0], matches["distances"][0]):
            distance = match[2]

            if distance < self.threshold:
                # with chromadb a lower distance means the vectors are more similar
                m = VectorMatch(text=match[0], metadata=match[1], distance=match[2])
                logger.info(f'[{self.name}] Matched vector text="{m.text}" threshold="{self.threshold}" distance="{m.distance}" id="{scan_id}"')
                scan_obj.results.append(m)

        if len(scan_obj.results) == 0:
            logger.info(f'[{self.name}] No matches found; id="{scan_id}"')

        return scan_obj
