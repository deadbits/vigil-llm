import uuid

from loguru import logger

from typing import Dict

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import SimilarityMatch

from vigil.embedding import Embedder
from vigil.embedding import cosine_similarity


class SimilarityScanner(BaseScanner):
    """ Compare the cosine similarity of the prompt and response """
    def __init__(self, config_dict: Dict):
        self.name = 'scanner:response-similarity'
        self.threshold = float(config_dict['threshold'])
        self.embedder = Embedder(
            config_dict['model_name'],
            config_dict['openai_key'] if 'openai_key' in config_dict else None,
        )

        logger.success('Loaded scanner.')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id={scan_id}')

        input_embedding = self.embedder.generate(scan_obj.prompt)
        output_embedding = self.embedder.generate(scan_obj.prompt_response)

        cosine_score = cosine_similarity(input_embedding, output_embedding)

        if cosine_score > self.threshold:
            m = SimilarityMatch(
                score=cosine_score,
                threshold=self.threshold,
                message='Response is not similar to prompt.',
            )
            logger.info('Response is not similar to prompt.')
            scan_obj.results.append(m)

        if len(scan_obj.results) == 0:
            logger.info('Response is similar to prompt.')

        return scan_obj
