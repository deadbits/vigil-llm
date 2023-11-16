import uuid
import nltk

from loguru import logger

from nltk.sentiment import SentimentIntensityAnalyzer

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import SentimentMatch


nltk.download('vader_lexicon')


class SentimentScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:sentiment'
        self.threshold = float(config_dict['threshold'])
        self.analyzer = SentimentIntensityAnalyzer()
        logger.success('Loaded scanner.')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id="{scan_id}"')

        prompt = scan_obj.prompt if scan_obj.prompt_response is None else scan_obj.prompt_response

        try:
            scores = self.analyzer.polarity_scores(prompt)
            logger.info(f'Sentiment scores: {scores} id="{scan_id}"')

            if scores['neg'] > self.threshold:
                logger.warning(f'Negative sentiment score above threshold; threshold={self.threshold} id="{scan_id}"')

            scan_obj.results.append(
                SentimentMatch(
                    threshold=self.threshold,
                    compound=scores['compound'],
                    negative=scores['neg'],
                    neutral=scores['neu'],
                    positive=scores['pos']
                )
            )
        except Exception as err:
            logger.error(f'Analyzer error: {err} id="{scan_id}"')
            return scan_obj

        return scan_obj
