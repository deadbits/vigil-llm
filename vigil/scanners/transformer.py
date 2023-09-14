import uuid
import logging

from transformers import pipeline

from vigil.schema import ModelMatch
from vigil.schema import BaseScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformerScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:transformer'
        self.model_name = config_dict['model']
        self.threshold = float(config_dict['threshold'])

        try:
            self.pipeline = pipeline('text-classification', model=self.model_name)
            logger.info(f'[{self.name}] Model loaded: {self.model_name}')
        except Exception as err:
            logger.error(f'[{self.name}] Failed to load model: {err}')

        logger.info(f'[{self.name}] Scanner loaded: {self.model_name}')

    def analyze(self, input_data: str, scan_uuid: uuid.uuid4) -> list:
        logger.info(f'[{self.name}] Performing scan; id="{scan_uuid}"')

        results, hits = [], []

        if input_data.strip() == '':
            logger.info(f'[{self.name}] No input data; id={scan_uuid}')
            return results

        try:
            hits = self.pipeline(
                input_data
            )
        except Exception as err:
            logger.error(f'[{self.name}] Pipeline error: {err}')
            return results

        if len(hits) > 0:
            for rec in hits:
                if rec['label'] == 'INJECTION':
                    if rec['score'] > self.threshold:
                        logger.info(f'[{self.name}] Detected prompt injection; score={rec["score"]} threshold={self.threshold} id={scan_uuid}')
                    else:
                        logger.info(
                            f'[{self.name}] Detected prompt injection below threshold (may warrant manual review); \
                            score={rec["score"]} threshold={self.threshold} id={scan_uuid}'
                        )

                    results.append(
                        ModelMatch(
                            model_name=self.model_name,
                            score=rec['score'],
                            label=rec['label'],
                            threshold=self.threshold,
                        )
                    )

        else:
            logger.info(f'[{self.name}] No hits returned by model; id={scan_uuid}')

        return results
