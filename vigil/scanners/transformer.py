import uuid

from loguru import logger

from transformers import pipeline

from vigil.schema import ModelMatch
from vigil.schema import ScanModel
from vigil.schema import BaseScanner


class TransformerScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:transformer'
        self.model_name = config_dict['model']
        self.threshold = float(config_dict['threshold'])

        try:
            self.pipeline = pipeline('text-classification', model=self.model_name)
            logger.info(f'Model loaded: {self.model_name}')
        except Exception as err:
            logger.error(f'Failed to load model: {err}')

        logger.success(f'Scanner loaded: {self.model_name}')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id={scan_id}')

        hits = []

        if scan_obj.prompt.strip() == '':
            logger.error(f'No input data; id={scan_id}')
            return scan_obj

        try:
            hits = self.pipeline(
                scan_obj.prompt
            )
        except Exception as err:
            logger.error(f'Pipeline error: {err} id={scan_id}')
            return scan_obj

        if len(hits) > 0:
            for rec in hits:
                if rec['label'] == 'INJECTION':
                    if rec['score'] > self.threshold:
                        logger.warning(f'Detected prompt injection; score={rec["score"]} threshold={self.threshold} id={scan_id}')
                    else:
                        logger.warning(
                            f'Detected prompt injection below threshold (may warrant manual review); \
                            score={rec["score"]} threshold={self.threshold} id={scan_id}'
                        )

                    scan_obj.results.append(
                        ModelMatch(
                            model_name=self.model_name,
                            score=rec['score'],
                            label=rec['label'],
                            threshold=self.threshold,
                        )
                    )

        else:
            logger.info(f'No hits returned by model; id={scan_id}')

        return scan_obj
