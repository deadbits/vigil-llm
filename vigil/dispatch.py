from typing import List, Dict
import math
import uuid

from loguru import logger  # type: ignore

from vigil.common import timestamp_str
from vigil.schema import BaseScanner, StatusEmum
from vigil.schema import ScanModel
from vigil.schema import ResponseModel


messages = {
    "scanner:yara": "Potential prompt injection detected: YARA signature(s)",
    "scanner:transformer": "Potential prompt injection detected: transformer model",
    "scanner:vectordb": "Potential prompt injection detected: vector similarity",
    "scanner:response-similarity": "Potential prompt injection detected: prompt-response similarity",
}


def calculate_entropy(text) -> float:
    prob = [text.count(c) / len(text) for c in set(text)]
    entropy = -sum(p * math.log2(p) for p in prob)
    return entropy


class Manager:
    def __init__(
        self,
        scanners: List[BaseScanner],
        auto_update: bool = False,
        update_threshold: int = 3,
        db_client=None,
        name: str = "input",
    ):
        self.name = f"dispatch:{name}"
        self.dispatcher = Scanner(scanners)
        self.auto_update = auto_update
        self.update_threshold = update_threshold
        self.db_client = db_client

        if self.auto_update:
            if self.db_client is None:
                logger.warning(f"{self.name} Auto-update disabled: db client is None")
            else:
                logger.info(
                    f"{self.name} Auto-update vectordb enabled: threshold={self.update_threshold}"
                )

    def perform_scan(self, prompt: str, prompt_response: str) -> dict:
        resp = ResponseModel(
            status=StatusEmum.SUCCESS,
            prompt=prompt,
            prompt_response=prompt_response,
            prompt_entropy=calculate_entropy(prompt),
        )

        if not prompt:
            resp.errors.append("Input prompt value is empty")
            resp.status = StatusEmum.FAILED
            logger.error(f"{self.name} Input prompt value is empty")
            return resp.dict()

        logger.info(f"{self.name} Dispatching scan request id={resp.uuid}")

        scan_results = self.dispatcher.run(
            prompt=prompt, prompt_response=prompt_response, scan_id=resp.uuid
        )

        total_matches = 0

        for scanner_name, results in scan_results.items():
            if "error" in results:
                resp.status = StatusEmum.PARTIAL
                resp.errors.append(f'Error in {scanner_name}: {results["error"]}')
            else:
                resp.results[scanner_name] = [{"matches": results}]
                if len(results) > 0 and scanner_name != "scanner:sentiment":
                    total_matches += 1

        for scanner_name, message in messages.items():
            if (
                scanner_name in scan_results
                and len(scan_results[scanner_name]) > 0
                and message not in resp.messages
            ):
                resp.messages.append(message)

        logger.info(f"{self.name} Total scanner matches: {total_matches}")
        if self.auto_update and (total_matches >= self.update_threshold):
            logger.info(
                f"{self.name} (auto-update) Adding detected prompt to db id={resp.uuid}"
            )
            doc_id = self.db_client.add_texts(
                [prompt],
                [
                    {
                        "uuid": resp.uuid,
                        "source": "auto-update",
                        "timestamp": timestamp_str(),
                        "threshold": self.update_threshold,
                    }
                ],
            )
            logger.success(
                f"{self.name} (auto-update) Successful doc_id={doc_id} id={resp.uuid}"
            )

        logger.info(f"{self.name} Returning response object id={resp.uuid}")

        return resp.dict()


class Scanner:
    def __init__(self, scanners: List[BaseScanner]):
        self.name = "dispatch:scan"
        self.scanners = scanners

    def run(self, prompt: str, scan_id: uuid.UUID, prompt_response: str) -> Dict:
        response = {}

        for scanner in self.scanners:
            scan_obj = ScanModel(
                prompt=prompt,
                prompt_response=(prompt_response if prompt_response.strip() else None),
            )

            try:
                logger.info(f"Running scanner: {scanner.name}; id={scan_id}")

                updated = scanner.analyze(scan_obj, scan_id)
                response[scanner.name] = [dict(res) for res in updated.results]
                logger.success(f"Successfully ran scanner: {scanner.name} id={scan_id}")

            except Exception as err:
                logger.error(
                    f"Failed to run scanner: {scanner.name}, Error: {str(err)} id={scan_id}"
                )
                response[scanner.name] = [{"error": str(err)}]

        return response
