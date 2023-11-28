import configparser
import os
from typing import Optional, List

from loguru import logger  # type: ignore


class Config:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_file):
            logger.error(f"Config file not found: {self.config_file}")
            raise ValueError(f"Config file not found: {self.config_file}")

        logger.info(f"Loading config file: {self.config_file}")
        self.config.read(config_file)

    def get_val(self, section: str, key: str) -> Optional[str]:
        answer = None

        try:
            answer = self.config.get(section, key)
        except Exception as err:
            logger.error(f"Config file missing section: {section} - {err}")

        return answer

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        try:
            return self.config.getboolean(section, key)
        except Exception as err:
            logger.error(
                f'Failed to parse boolean - returning default "False": {section} - {err}'
            )
            return default

    def get_scanner_config(self, scanner_name):
        return {
            key: self.get_val(f"scanner:{scanner_name}", key)
            for key in self.config.options(f"scanner:{scanner_name}")
        }

    def get_general_config(self):
        return {
            section: dict(self.config.items(section))
            for section in self.config.sections()
        }

    def get_scanner_names(self, scanner_type: str) -> List[str]:
        return str(self.get_val("scanners", scanner_type)).split(",")
