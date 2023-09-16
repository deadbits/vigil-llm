import os
import sys
import logging

import configparser

from typing import Optional


class Config:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_file):
            logging.error(f'[config] Config file not found: {self.config_file}')
            sys.exit(1)

        logging.info(f'[config] Loading config file: {self.config_file}')
        self.config.read(config_file)

    def get_val(self, section: str, key: str) -> Optional[str]:
        answer = None

        try:
            answer = self.config.get(section, key)
        except Exception as err:
            logging.error(f'[config] Config file missing section: {section} - {err}')

        return answer

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        try:
            return self.config.getboolean(section, key)
        except Exception as err:
            logging.error(f'[config] Failed to parse boolean - returning default "False": {section} - {err}')
            return default
