from typing import List
import uuid
import logging

import yaml  # type: ignore

from vigil.schema import BaseScanner, ScanModel
from vigil.core.llm import LLM


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RelevanceScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = "scanner:relevance"
        self.prompt_path = (
            config_dict["prompt"] if "prompt_path" in config_dict else None
        )

        if self.prompt_path is None:
            logger.error(f"[{self.name}] prompt path is not defined; check config")
            raise ValueError("[scanner:relevance] prompt path is not defined")

        self.llm = LLM(
            model_name=config_dict["model_name"],
            api_key=config_dict["api_key"] if "api_key" in config_dict else None,
            api_base=config_dict["api_base"] if "api_base" in config_dict else None,
        )

    def load_prompt(self) -> dict:
        logger.info(f"[{self.name}] Loading prompt from {self.prompt_path}")

        with open(self.prompt_path, "r") as fp:
            data = yaml.safe_load(fp)
        return data

    def analyze(self, input_data: str, scan_id: uuid.UUID = uuid.uuid4()) -> ScanModel:
        logger.info(f'[{self.name}] performing scan; id="{scan_id}"')

        prompt = self.load_prompt()["prompt"]
        prompt = prompt.format(input_data=input_data)

        try:
            output = self.llm.generate(input_data, content_only=True)
            logger.info(f"[{self.name}] LLM output: {output}")
        except Exception as err:
            logger.error(
                f"[{self.name}] Failed to perform relevance scan (call to LLM): {err}"
            )
            raise

        return output
