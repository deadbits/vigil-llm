import uuid
import logging

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TextClassificationPipeline,
)

from vigil.schema import ModelMatch
from vigil.schema import BaseScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformerScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:transformer'
        self.model_name = config_dict['model']
        self.threshold = config_dict['threshold']
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            logger.info(f'[{self.name}] Model loaded: {self.model_name}')
        except Exception as err:
            logger.error(f'[{self.name}] Failed to load model: {err}')

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logger.info(f'[{self.name}] Tokenizer loaded: {self.model_name}')
        except Exception as err:
            logger.error(f'[{self.name}] Failed to load tokenizer: {err}')

        self.pipeline = TextClassificationPipeline(
            model=self.model, tokenizer=self.tokenizer
        )
        logger.info(f'[{self.name}] Pipeline loaded: {self.model_name}')

    def analyze(self, input_data: str, scan_uuid: uuid.uuid4) -> list:
        logger.info(f'[{self.name}] Performing scan; id="{scan_uuid}"')

        score = 0.0
        results = []

        if input_data.strip() == '':
            logger.info(f'[{self.name}] No input data; id={scan_uuid}')
            return results

        try:
            result = self.pipeline(
                input_data,
                truncation=True,
                max_length=self.tokenizer.model_max_length
            )
            score = round(
                result[0]['score'] if result[0]['label'] == 'INJECTION' else 1 - result[0]['score'], 2
            )
        except Exception as err:
            logger.error(f'[{self.name}] Pipeline error: {err}')
            return results

        if score > float(self.threshold):
            logger.info(f'[{self.name}] Detected prompt injection; score={score} threshold={self.threshold} id={scan_uuid}')
            results.append(
                ModelMatch(
                    model_name=self.model_name,
                    score=score,
                    threshold=self.threshold,
                )
            )

        return results
