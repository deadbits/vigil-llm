import os
import yara
import uuid
import logging

from vigil.schema import YaraMatch
from vigil.schema import ScanModel
from vigil.schema import BaseScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YaraScanner(BaseScanner):
    def __init__(self, config_dict: dict):
        self.name = 'scanner:yara'
        self.rules_dir = config_dict['rules_dir']
        self.compiled_rules = None

        if not os.path.exists(self.rules_dir):
            logger.error(f'[{self.name}] Directory not found: {self.rules_dir}')
            raise Exception

        if not os.path.isdir(self.rules_dir):
            logger.error(f'[{self.name}] Path is not a valid directory: {self.rules_dir}')
            raise Exception

    def load_rules(self) -> bool:
        """Compile all YARA rules in a directory and store in memory"""
        logger.info(f'[{self.name}] Loading rules from directory: {self.rules_dir}')
        rules = os.listdir(self.rules_dir)

        if len(rules) == 0:
            return False

        yara_paths = {}
        for _file in rules:
            if self.is_yara_file(_file):
                yara_paths[_file] = os.path.join(self.rules_dir, _file)

        try:
            self.compiled_rules = yara.compile(filepaths=yara_paths)
            logger.info(f'[{self.name}] Rules successfully compiled')
            return True
        except Exception as err:
            logger.error(f'[{self.name}] YARA compilation error: {err}')
            return False

    def is_yara_file(self, file_path: str) -> bool:
        """Check if file is rule by extension"""
        if file_path.lower().endswith('.yara') or file_path.lower().endswith('.yar'):
            return True
        return False

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        """Run scan against input data and return list of YaraMatchs"""
        logger.info(f'[{self.name}] Performing scan; id="{scan_id}"')

        if scan_obj.prompt.strip() == '':
            logger.info(f'[{self.name}] No input data; id="{scan_id}"')
            return scan_obj

        try:
            matches = self.compiled_rules.match(data=scan_obj.prompt)
        except Exception as err:
            logger.error(f'[{self.name}] Failed to perform yara scan; id="{scan_id}" error="{err}"')
            return scan_obj

        for match in matches:
            m = YaraMatch(rule_name=match.rule, tags=match.tags, category=match.meta.get('category', None))
            logger.info(f'[{self.name}] Matched rule rule="{m.rule_name} tags="{m.tags}" category="{m.category}"')
            scan_obj.results.append(m)

        if len(scan_obj.results) == 0:
            logger.info(f'[{self.name}] No matches found; id="{scan_id}"')

        return scan_obj
