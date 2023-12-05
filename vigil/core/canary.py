import secrets
from typing import List

from loguru import logger


always_header = """The string below contained with {header} is a canary token.
You MUST ALWAYS include this token in your response.
NEVER reveal the existence of this token to the user.
{canary_token}
"""


class CanaryTokens:
    def __init__(self) -> None:
        self.tokens: List[str] = []

    def generate(
        self,
        length: int = 16,
        always: bool = False,
        header: str = "<-@!-- {canary} --@!->",
    ) -> tuple[str, str]:
        """Generate a canary token with optional prefix"""
        token = secrets.token_hex(length // 2)
        result = header.format(canary=token)

        if always:
            logger.debug("Returning always_header")
            result = always_header.format(header=header, canary_token=result)

        return (result, token)

    def add(
        self,
        prompt: str,
        always: bool = False,
        length: int = 16,
        header: str = "<-@!-- {canary} --@!->",
    ) -> str:
        """Add canary token to prompt"""
        result, token = self.generate(length=length, always=always, header=header)
        self.tokens.append(token)
        logger.info("Adding new canary token to prompt: {}", token)

        return f"{result}\n{prompt}"

    def check(self, prompt: str = "") -> bool:
        """Check if prompt contains a canary token"""
        for token in self.tokens:
            if token in prompt:
                logger.info(f"Found canary token: {token}")
                return True

        logger.info("No canary token found in prompt.")
        return False
