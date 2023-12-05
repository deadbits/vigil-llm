import uuid
from loguru import logger
from vigil.core.embedding import Embedder, cosine_similarity
from vigil.registry import Registration
from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import SimilarityMatch


@Registration.scanner(name="similarity", requires_config=True, requires_embedding=True)
class SimilarityScanner(BaseScanner):
    """Compare the cosine similarity of the prompt and response"""

    def __init__(self, threshold: float, embedder: Embedder):
        self.name = "scanner:response-similarity"
        self.threshold = float(threshold)
        self.embedder = embedder

        logger.success("Loaded scanner")

    def analyze(
        self, scan_obj: ScanModel, scan_id: uuid.UUID = uuid.uuid4()
    ) -> ScanModel:
        logger.info(f"Performing scan; id={scan_id}")

        input_embedding = self.embedder.generate(scan_obj.prompt)
        if scan_obj.prompt_response is not None:
            output_embedding = self.embedder.generate(scan_obj.prompt_response)
        else:
            output_embedding = []

        cosine_score = cosine_similarity(input_embedding, output_embedding)

        if cosine_score > self.threshold:
            logger.warning("Response is not similar to prompt.")
            scan_obj.results.append(
                SimilarityMatch(
                    score=cosine_score,
                    threshold=self.threshold,
                    message="Response is not similar to prompt.",
                ).model_dump()
            )

        if len(scan_obj.results) == 0:
            logger.info("Response is similar to prompt.")

        return scan_obj
