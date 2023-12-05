from typing import Optional
import litellm  # type: ignore
from loguru import logger

from vigil.schema import ScanModel


class LLM:
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        self.name = "llm"
        litellm.api_key = api_key
        self.api_base = api_base

        if model_name not in litellm.model_list:
            logger.error(f"Model name not supported: {model_name}")
            raise ValueError("Model name not supported")

        if not litellm.check_valid_key(model=model_name, api_key=api_key):
            logger.error(f"Invalid API key for model: {model_name}")
            raise ValueError("Invalid API key for model")

        self.model_name = model_name
        logger.info("Loaded LLM API.")

    def generate(
        self, prompt: ScanModel, content_only: Optional[bool] = False
    ) -> ScanModel:
        """Call configured LLM model with litellm"""
        logger.info(f"Calling model: {self.model_name}")

        messages = [{"content": prompt.prompt, "role": "user"}]

        try:
            output = litellm.completion(
                model=self.model_name,
                messages=messages,
                api_base=self.api_base if self.api_base else None,
            )
        except Exception as err:
            logger.error("Failed to generate output for input data: %s", err)
            raise

        return output["choices"][0]["message"]["content"] if content_only else output
