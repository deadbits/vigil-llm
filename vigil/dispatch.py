import uuid
import math

from loguru import logger

from typing import List, Dict

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import ResponseModel

from vigil.common import timestamp_str


messages = {
    'scanner:yara': 'Potential prompt injection detected: YARA signature(s)',
    'scanner:transformer': 'Potential prompt injection detected: transformer model',
    'scanner:vectordb': 'Potential prompt injection detected: vector similarity',
    'scanner:response-similarity': 'Potential prompt injection detected: prompt-response similarity'
}


def calculate_entropy(text):
    prob = [text.count(c) / len(text) for c in set(text)]
    entropy = -sum(p * math.log2(p) for p in prob)
    return entropy


class Manager:
    def __init__(self,
                 scanners: List[BaseScanner],
                 auto_update: bool = False,
                 update_threshold: int = 3,
                 db_client=None,
                 name: str = 'input'):
        self.name = f'dispatch:{name}'
        self.dispatcher = Scanner(scanners)
        self.auto_update = auto_update
        self.update_threshold = update_threshold
        self.db_client = db_client

        if self.auto_update:
            if self.db_client is None:
                logger.warn('{self.name} Auto-update disabled: db client is None')
            else:
                logger.info(f'{self.name} Auto-update vectordb enabled: threshold={self.update_threshold}')

    def perform_scan(self, input_prompt: str, input_resp: str = None) -> dict:
        resp = ResponseModel(
            status='success',
            timestamp=timestamp_str(),
            prompt=input_prompt,
            prompt_response=input_resp,
            prompt_entropy=calculate_entropy(input_prompt),
        )

        resp.uuid = str(resp.uuid)

        if not input_prompt:
            resp.errors.append('Input prompt value is empty')
            resp.status = 'failed'
            logger.error('{self.name} Input prompt value is empty')
            return resp.dict()

        logger.info(f'{self.name} Dispatching scan request id={resp.uuid}')

        scan_results = self.dispatcher.run(
            input_prompt=input_prompt,
            input_resp=input_resp,
            scan_id={resp.uuid}
        )

        total_matches = 0

        for scanner_name, results in scan_results.items():
            if 'error' in results:
                resp.status = 'partial_success'
                resp.errors.append(f'Error in {scanner_name}: {results["error"]}')
            else:
                # update for each matching scanner, not the number of results
                # within an each individual scanner
                resp.results[scanner_name] = {'matches': results}
                if len(results) > 0:
                    total_matches += 1

        for scanner_name, message in messages.items():
            if scanner_name in scan_results and len(scan_results[scanner_name]) > 0 \
                    and message not in resp.messages:
                resp.messages.append(message)

        logger.info(f'{self.name} Total scanner matches: {total_matches}')
        if self.auto_update and (total_matches == self.update_threshold or
                                 total_matches > self.update_threshold):
            logger.info('{self.name} (auto-update) Adding detected prompt to db id={resp.uuid}')
            doc_id = self.db_client.add_texts(
                [input_prompt],
                [
                    {
                        'uuid': resp.uuid,
                        'source': 'auto-update',
                        'timestamp': timestamp_str(),
                        'threshold': self.update_threshold
                    }
                ]
            )
            logger.success(f'{self.name} (auto-update) Successful doc_id={doc_id} id={resp.uuid}')

        logger.info(f'{self.name} Returning response object id={resp.uuid}')

        return resp.dict()


class Scanner:
    def __init__(self, scanners: List[BaseScanner]):
        self.name = 'dispatch:scan'
        self.scanners = scanners

    def run(self, input_prompt: str, scan_id: uuid.uuid4, input_resp: str = None) -> Dict:
        response = {}

        for scanner in self.scanners:
            scan_obj = ScanModel(
                prompt=input_prompt,
                prompt_response=input_resp
            )

            try:
                logger.info(f'Running scanner: {scanner.name}; id={scan_id}')

                updated = scanner.analyze(scan_obj, scan_id)
                response[scanner.name] = [res.dict() for res in updated.results]
                logger.success(f'Successfully ran scanner: {scanner.name} id={scan_id}')

            except Exception as err:
                logger.error(f'Failed to run scanner: {scanner.name}, Error: {str(err)} id={scan_id}')
                response[scanner.name] = {'error': str(err)}

        return response
