import logging
import openai
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cosine_similarity(embedding1: List, embedding2: List) -> float:
    """ Get cosine similarity between two embeddings """
    product = np.dot(embedding1, embedding2)
    norm = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    return product / norm


class Embedder:
    def __init__(self, model_name: str, openai_key: str = None):
        self.name = 'embedder'

        if model_name == 'openai':
            logger.info(f'[{self.name}] Using OpenAI embedding function')
            if openai_key is None:
                logger.error(f'[{self.name}] No OpenAI API key passed to embedder.')
                raise ValueError("No OpenAI API key provided.")

            openai.api_key = openai_key
            try:
                openai.Model.list()
            except Exception as err:
                logger.error(f'[{self.name}] Failed to connect to OpenAI API: {err}')
                raise Exception(f"Connection to OpenAI API failed: {err}")

            self.model_name = 'openai'
            self.embed_func = self.openai

        else:
            logger.info(f'[{self.name}] Using SentenceTransformer embedding function: {model_name}')
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f'[{self.name}] Loaded model: {model_name}')
            except Exception as err:
                logger.error(f'[{self.name}] Failed to load model: {model_name} error="{err}"')
                raise ValueError(f"Failed to load SentenceTransformer model: {err}")

            self.model_name = model_name
            self.embed_func = self.transformer

        logger.info(f'[{self.name}] Loaded embedder.')

    def generate(self, input_data: str) -> List:
        return self.embed_func(input_data)

    def openai(self, input_data: str) -> List:
        logger.info(f'[{self.name}] Generating embedding with OpenAI')

        try:
            response = openai.Embedding.create(
                input=input_data, model='text-embedding-ada-002'
            )
            data = response['data'][0]
            return data['embedding']
        except Exception as err:
            logger.error(f'[{self.name}] Failed to generate embedding: {err}')
            return []

    def transformer(self, input_data: str) -> List:
        logger.info(f'[{self.name}] Generating embedding with SentenceTransformer')

        try:
            results = self.model.encode(input_data).tolist()
            return results
        except Exception as err:
            logger.error(f'[{self.name}] Failed to encode input data: {err}')
            return []
