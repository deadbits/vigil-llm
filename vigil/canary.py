import secrets

from loguru import logger


class CanaryTokens:
    def __init__(self):
        self.tokens = []

    def generate(self, prefix: str = '', length: int = 16) -> str:
        """Generate a canary token with optional prefix"""
        return prefix + secrets.token_hex(length // 2)

    def add(self,
            prompt: str,
            length: int = 16,
            header: str = '<-@!-- {canary} --@!->',
            prefix: str = '') -> str:
        """Add canary token to prompt"""
        canary = self.generate(prefix=prefix, length=length)
        self.tokens.append(canary)
        logger.info(f'Adding new canary token to prompt: {canary}')
        return header.format(canary=canary) + '\n' + prompt

    def check(self, prompt: str = '') -> bool:
        """Check if prompt contains a canary token"""
        for token in self.tokens:
            if token in prompt:
                logger.info(f'Found canary token: {token}')
                return True

        logger.info('No canary token found in prompt.')
        return False
