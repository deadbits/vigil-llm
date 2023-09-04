import uuid
import logging

import openai

from vigil.schema import BaseScanner
from vigil.schema import ModerationMatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIModeration(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:moderation-openai'
        openai.api_key = config_dict['openai_api_key']

        try:
            openai.Model.list()
            logger.info(f'[{self.name}] Loaded scanner.')
        except Exception as err:
            logger.error(f'[{self.name}] Failed to set OpenAI API key error="{err}"')
            raise Exception

    def analyze(self, input_data: str, scan_uuid: uuid.uuid4) -> list:
        logger.info(f'[{self.name}] Performing scan; id="{scan_uuid}"')
        results = []

        response = openai.Moderation.create(input=input_data)
        model_name = response['model']

        output = response['results'][0]

        for item in output['categories']:
            if item:
                score = output['category_scores'][item]
                match = ModerationMatch(model_name=model_name, category=item, score=score)
                logger.info(f'[scanner:moderation-openai] Matched category="{item}" score="{score}" id="{scan_uuid}"')
                results.append(match)

        return results
