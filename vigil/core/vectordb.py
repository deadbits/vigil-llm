# https://github.com/deadbits/vigil-llm
import os
from typing import List, Optional
import chromadb  # type: ignore
from chromadb.config import Settings  # type: ignore
from chromadb.utils import embedding_functions  # type: ignore
from loguru import logger  # type: ignore

from vigil.common import uuid4_str
from vigil.core.config import Config


class VectorDB:
    def __init__(
        self,
        model: str,
        collection: str,
        db_dir: str,
        n_results: int,
        openai_key: Optional[str] = None,
    ):
        """Initialize Chroma vector db client"""

        self.name = "database:vector"

        if model == "openai":
            logger.info("Using OpenAI embedding function")
            if openai_key is None or openai_key.strip() == "":
                logger.debug("Using OPENAI_API_KEY environment variable for API Key")
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key is None or openai_key.strip() == "":
                    logger.error("OPENAI_API_KEY environment variable is not set")
                    raise ValueError("OPENAI_API_KEY environment variable is not set")
            else:
                logger.debug(
                    "Using OpenAI API Key from config file: '{}...{}'",
                    openai_key[:3],
                    openai_key[-3],
                )
            self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_key, model_name="text-embedding-ada-002"
            )
        elif model is not None:
            # logger.info(
            # f'Using SentenceTransformer embedding function: {model}'
            # )
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model
            )
        else:
            raise ValueError(
                "vectordb.model is not set in config file, needs to be 'openai' or a SentenceTransformer model name"
            )

        self.collection = collection
        self.db_dir = db_dir
        if n_results is not None:
            self.n_results = int(n_results)
        else:
            self.n_results = 5

        if not hasattr(self.embed_fn, "__call__"):
            logger.error("Embedding function is not callable")
            raise ValueError("Embedding function is not a function")

        self.client = chromadb.PersistentClient(
            path=self.db_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.get_or_create_collection(self.collection)
        logger.success("Loaded database")

    def get_or_create_collection(self, name: str):
        logger.info(f"Using collection: {name}")
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        return self.collection

    def add_texts(self, texts: List[str], metadatas: List[dict]):
        success = False

        logger.info(f"Adding {len(texts)} texts")
        for metadata in metadatas:
            for key, value in metadata.items():
                if not isinstance(value, str):
                    metadata[key] = str(value)
        ids = [uuid4_str() for _ in range(len(texts))]

        try:
            self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
            success = True
        except Exception as err:
            logger.error(f"Failed to add texts to collection: {err}")

        return (success, ids)

    def add_embeddings(
        self, texts: List[str], embeddings: List[List], metadatas: List[dict]
    ):
        success = False

        logger.info(f"Adding {len(texts)} embeddings")
        ids = [uuid4_str() for _ in range(len(texts))]

        try:
            self.collection.add(
                documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids
            )
            success = True
        except Exception as err:
            logger.error(f"Failed to add texts to collection: {err}")

        return (success, ids)

    def query(self, text: str) -> chromadb.QueryResult:
        logger.info(f"Querying database for: {text}")
        return self.collection.query(query_texts=[text], n_results=self.n_results)


def setup_vectordb(conf: Config) -> VectorDB:
    full_config = conf.get_general_config()
    params = full_config.get("vectordb", {})
    params.update(full_config.get("embedding", {}))
    for key in ["collection", "db_dir", "n_results"]:
        if key not in params:
            raise ValueError(f"config needs key {key}")
    return VectorDB(**params)


# def setup_vectordb(conf: Config) -> VectorDB:
#     full_config = conf.get_general_config()
#     params = full_config.get("vectordb", {})

#     return VectorDB(
#         model=params.get("model"),
#         collection=params.get("collection"),
#         db_dir=params.get("db_dir"),
#         n_results=params.get("n_results"),
#         openai_key=params.get("openai_key"),
#     )
