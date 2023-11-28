import os
import numpy as np  # type: ignore

from openai import OpenAI  # type: ignore

from loguru import logger  # type: ignore

from typing import List, Optional
from sentence_transformers import SentenceTransformer  # type: ignore


def cosine_similarity(embedding1: List, embedding2: List) -> float:
    """Get cosine similarity between two embeddings"""
    product = np.dot(embedding1, embedding2)
    norm = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    return product / norm


class Embedder:
    def __init__(self, model: str, openai_key: Optional[str] = None, **kwargs):
        self.name = "embedder"
        self.model_name = model

        if model == "openai":
            logger.info("Using OpenAI")
            if openai_key is None:
                # try and get it from the environment
                openai_key = os.environ.get("OPENAI_API_KEY", None)
                if openai_key is None:
                    msg = "No OpenAI API key passed to embedder, needs to be in configuration or OPENAI_API_KEY env variable."
                    logger.error(msg)
                    raise ValueError(msg)

            self.client = OpenAI(api_key=openai_key)
            try:
                self.client.models.list()
            except Exception as err:
                logger.error(f"Failed to connect to OpenAI API: {err}")
                raise Exception(f"Connection to OpenAI API failed: {err}")

            self.embed_func = self._openai

        else:
            logger.info(f"Using SentenceTransformer: {model}")
            try:
                self.model = SentenceTransformer(model)
                logger.success(f"Loaded model: {model}")
            except Exception as err:
                logger.error(f'Failed to load model: {model} error="{err}"')
                raise ValueError(f"Failed to load SentenceTransformer model: {err}")

            self.embed_func = self._transformer

        logger.success("Loaded embedder")

    def generate(self, input_data: str) -> List:
        logger.info(f"Generating with: {self.model_name}")
        return self.embed_func(input_data)

    def _openai(self, input_data: str) -> List:
        try:
            response = self.client.embeddings.create(
                input=input_data, model="text-embedding-ada-002"
            )
            data = response.data[0]
            return data.embedding
        except Exception as err:
            logger.error(f"Failed to generate embedding: {err}")
            return []

    def _transformer(self, input_data: str) -> List:
        try:
            results = self.model.encode(input_data).tolist()
            return results
        except Exception as err:
            logger.error(f"Failed to generate embedding: {err}")
            return []
