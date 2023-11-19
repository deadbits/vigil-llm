import uuid

from loguru import logger

from typing import Optional

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import SimilarityMatch

from vigil.core.embedding import Embedder
from vigil.core.embedding import cosine_similarity


class SimilarityScanner(BaseScanner):
    """ Compare the cosine similarity of the prompt and response """
    def __init__(self, model: str, threshold: float, openai_key: Optional[str] = None):
        self.name = 'scanner:response-similarity'
        self.threshold = threshold
        self.embedder = Embedder(
            model_name=model,
            openai_key=openai_key,
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
            logger.warning('Response is not similar to prompt.')
            scan_obj.results.append(m)

        if len(scan_obj.results) == 0:
            logger.info('Response is similar to prompt.')

        return scan_obj
