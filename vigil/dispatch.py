from typing import List, Dict, Optional
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
                logger.warning("{} Auto-update disabled: db client is None", self.name)
            else:
                logger.info(
                    "{} Auto-update vectordb enabled: threshold={}",
                    self.name,
                    self.update_threshold,
                )

    def perform_scan(self, prompt: str, prompt_response: Optional[str] = None) -> dict:
        resp = ResponseModel(
            status=StatusEmum.SUCCESS,
            prompt=prompt,
            prompt_response=prompt_response,
            prompt_entropy=calculate_entropy(prompt),
        )

        if not prompt:
            resp.errors.append("Input prompt value is empty")
            resp.status = StatusEmum.FAILED
            logger.error("{} Input prompt value is empty", self.name)
            return resp.model_dump()

        logger.info("{} Dispatching scan request id={}", self.name, resp.uuid)

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

        logger.info("{} Total scanner matches: {}", self.name, total_matches)
        if self.auto_update and (total_matches >= self.update_threshold):
            logger.info(
                "{} (auto-update) Adding detected prompt to db id={}",
                self.name,
                resp.uuid,
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
                "{} (auto-update) Successful doc_id={} id={resp.uuid}",
                self.name,
                doc_id,
                resp.uuid,
            )

        logger.info("{} Returning response object id={}"), self.name, resp.uuid

        return resp.model_dump()


class Scanner:
    def __init__(self, scanners: List[BaseScanner]):
        self.name = "dispatch:scan"
        self.scanners = scanners

    def run(
        self, prompt: str, scan_id: uuid.UUID, prompt_response: Optional[str]
    ) -> Dict:
        response = {}

        for scanner in self.scanners:
            if prompt_response is not None and prompt_response.strip() == "":
                prompt_response = None
            scan_obj = ScanModel(
                prompt=prompt,
                prompt_response=prompt_response,
            )

            try:
                logger.info("Running scanner: {}; id={}", scanner.name, scan_id)

                updated = scanner.analyze(scan_obj, scan_id)
                response[scanner.name] = [dict(res) for res in updated.results]
                logger.success(
                    "Successfully ran scanner: {} id={}", scanner.name, scan_id
                )

            except Exception as err:
                logger.error(
                    "Failed to run scanner: {}, Error: {} id={}",
                    scanner.name,
                    err,
                    scan_id,
                )
                response[scanner.name] = [{"error": str(err)}]

        return response
