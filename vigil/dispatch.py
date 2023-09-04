import logging

from typing import List, Dict

from vigil.schema import BaseScanner
from vigil.schema import ScanModel

from vigil.common import timestamp_str


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Manager:
    def __init__(self, scanners: List[BaseScanner]):
        self.name = 'dispatch:mgr'
        self.dispatcher = Scanner(scanners)

    def perform_scan(self, input_prompt: str) -> dict:
        response = {
            'status': 'success',
            'timestamp': timestamp_str(),
            'input_prompt': '',
            'messages': [],
            'errors': [],
            'results': {
                'scanner:yara': {'matches': []},
                'scanner:vectordb': {'matches': [], 'threshold': 0.2}
            }
        }

        if not input_prompt:
            response['errors'].append('Input prompt value is empty')
            logger.error(f'[{self.name}] input prompt value is empty')
            return response

        scan_obj = ScanModel(input_prompt=input_prompt)
        logging.info(f'[{self.name}] New scan object; id={scan_obj.uuid}')

        scan_results = self.dispatcher.run(scan_obj.input_prompt, scan_obj.uuid)

        for scanner_name, results in scan_results.items():
            if 'error' in results:
                response['status'] = 'partial_success'
                response['errors'].append(f'Error in {scanner_name}: {results["error"]}')
            else:
                response['results'][scanner_name] = {'matches': results}

            # Additional logic for message updates
            if scanner_name == 'scanner:yara' and len(results) > 0:
                if 'Potential prompt injection detected: YARA signature(s)' not in response['messages']:          
                    response['messages'].append('Potential prompt injection detected: YARA signature(s)')

            if scanner_name == 'scanner:transformer' and len(results) > 0:
                if 'Potential prompt injection detected: transformer model' not in response['messages']:
                    response['messages'].append('Potential prompt injection detected: transformer model')

            if scanner_name == 'scanner:vectordb' and len(results) > 0:
                if 'Potential prompt injection detected: vector similarity' not in response['messages']:
                    response['messages'].append('Potential prompt injection detected: vector similarity')

        response['input_prompt'] = scan_obj.input_prompt
        logging.info(f'[{self.name}] returning response: {response}')

        return response


class Scanner:
    def __init__(self, scanners: List[BaseScanner]):
        self.name = 'dispatch:scan'
        self.scanners = scanners

    def run(self, input_data: str, scan_uuid: str) -> Dict:
        logger.info(f'[{self.name}] new task id={scan_uuid}')
        response = {}

        for scanner in self.scanners:
            try:
                logger.info(f'[{self.name}] Running scanner: {scanner.name}')
                results = scanner.analyze(input_data, scan_uuid)
                response[scanner.name] = [res.dict() for res in results]
                logger.info(f'[{self.name}] Successfully ran scanner: {scanner.name}')

            except Exception as err:
                logger.error(f'[{self.name}] Failed to run scanner: {scanner.name}, Error: {str(err)}')
                response[scanner.name] = {'error': str(err)}

        return response
