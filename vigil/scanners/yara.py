import os
import uuid

from loguru import logger  # type: ignore
import yara  # type: ignore

from vigil.schema import YaraMatch
from vigil.schema import ScanModel
from vigil.schema import BaseScanner

from vigil.registry import Registration


@Registration.scanner(name="yara", requires_config=True)
class YaraScanner(BaseScanner):
    def __init__(self, rules_dir: str):
        self.name = "scanner:yara"
        self.rules_dir = rules_dir
        self.compiled_rules = None

        if not os.path.exists(self.rules_dir):
            logger.error(f"Directory not found: {self.rules_dir}")
            raise Exception

        if not os.path.isdir(self.rules_dir):
            logger.error(f"Path is not a valid directory: {self.rules_dir}")
            raise Exception

        self.load_rules()
        logger.success("Loaded scanner")

    def load_rules(self) -> None:
        """Compile all YARA rules in a directory and store in memory"""
        logger.info(f"Loading rules from directory: {self.rules_dir}")
        rules = os.listdir(self.rules_dir)

        if len(rules) == 0:
            return

        yara_paths = {}
        for _file in rules:
            if self.is_yara_file(_file):
                yara_paths[_file] = os.path.join(self.rules_dir, _file)

        try:
            self.compiled_rules = yara.compile(filepaths=yara_paths)
        except Exception as err:
            logger.error(f"YARA compilation error: {err}")
            raise err

    def is_yara_file(self, file_path: str) -> bool:
        """Check if file is rule by extension"""
        if file_path.lower().endswith(".yara") or file_path.lower().endswith(".yar"):
            return True
        return False

    def analyze(
        self, scan_obj: ScanModel, scan_id: uuid.UUID = uuid.uuid4()
    ) -> ScanModel:
        """Run scan against input data and return list of YaraMatchs"""
        logger.info(f'Performing scan; id="{scan_id}"')

        if scan_obj.prompt.strip() == "":
            logger.error(f'No input data; id="{scan_id}"')
            return scan_obj

        try:
            if self.compiled_rules is None:
                logger.error("No rules to check!")
                return scan_obj
            matches = self.compiled_rules.match(data=scan_obj.prompt)
        except Exception as err:
            logger.error(f'Failed to perform yara scan; id="{scan_id}" error="{err}"')
            return scan_obj

        for match in matches:
            m = YaraMatch(
                rule_name=match.rule,
                tags=match.tags,
                category=match.meta.get("category", None),
            )
            logger.warning(
                f'Matched rule rule="{m.rule_name} tags="{m.tags}" category="{m.category}"'
            )
            scan_obj.results.append(m)

        if len(scan_obj.results) == 0:
            logger.info(f'No matches found; id="{scan_id}"')

        return scan_obj
