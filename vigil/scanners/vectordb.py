import uuid

from loguru import logger

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import VectorMatch


class VectorScanner(BaseScanner):
    def __init__(self, config_dict: dict, db_client):
        self.name = 'scanner:vectordb'
        self.database = db_client
        self.threshold = config_dict['threshold']
        logger.info('Loaded scanner.')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id="{scan_id}"')

        try:
            matches = self.database.query(scan_obj.prompt)
        except Exception as err:
            logger.error(f'Failed to perform vector scan; id="{scan_id}" error="{err}"')
            return scan_obj

        for match in zip(matches["documents"][0], matches["metadatas"][0], matches["distances"][0]):
            distance = match[2]

            if distance < self.threshold:
                # with chromadb a lower distance means the vectors are more similar
                m = VectorMatch(text=match[0], metadata=match[1], distance=match[2])
                logger.info(f'Matched vector text="{m.text}" threshold="{self.threshold}" distance="{m.distance}" id="{scan_id}"')
                scan_obj.results.append(m)

        if len(scan_obj.results) == 0:
            logger.info(f'No matches found; id="{scan_id}"')

        return scan_obj
