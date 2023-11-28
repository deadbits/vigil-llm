from loguru import logger  # type: ignore

from typing import List, Optional, Callable

from vigil.dispatch import Manager
from vigil.schema import BaseScanner

from vigil.core.config import Config
from vigil.core.canary import CanaryTokens
from vigil.core.vectordb import VectorDB, setup_vectordb
from vigil.core.embedding import Embedder

from vigil.registry import ScannerRegistry


class Vigil:
    vectordb: Optional[VectorDB] = None
    embedder: Optional[Callable] = None

    def __init__(self, config_path: str):
        self._config = Config(config_path)
        self._initialize_vectordb()
        self._initialize_embedder()

        self._input_scanners: List[BaseScanner] = self._setup_scanners(
            self._config.get_scanner_names("input_scanners")
        )
        self._output_scanners: List[BaseScanner] = self._setup_scanners(
            self._config.get_scanner_names("output_scanners")
        )

        self.canary_tokens = CanaryTokens()
        self.input_scanner = self._create_manager(
            name="input", scanners=self._input_scanners
        )
        self.output_scanner = self._create_manager(
            name="output", scanners=self._output_scanners
        )

    def _initialize_embedder(self):
        full_config = self._config.get_general_config()
        params = full_config.get("embedding", {})
        self.embedder = Embedder(**params)

    def _initialize_vectordb(self):
        self.vectordb = setup_vectordb(self._config)

    def _setup_scanners(self, scanner_names: List[str]) -> List[BaseScanner]:
        scanners = []

        for name in scanner_names:
            try:
                metadata = ScannerRegistry.get_scanner_metadata(name)
            except ValueError as err:
                logger.error(err)
                raise err

            scanner_config = None
            vectordb = None
            embedder = None

            if metadata.get("requires_config", False):
                scanner_config = self._config.get_scanner_config(name)

            if metadata.get("requires_vectordb", False):
                vectordb = self.vectordb

            if metadata.get("requires_embedding", False):
                embedder = self.embedder

            scanner = ScannerRegistry.create_scanner(
                name=name, config=scanner_config, vectordb=vectordb, embedder=embedder
            )
            scanners.append(scanner)

        return scanners

    def _create_manager(self, name: str, scanners: List[BaseScanner]) -> Manager:
        manager_config = self._config.get_general_config()
        auto_update = manager_config.get("auto_update", {}).get("enabled", False)
        update_threshold = int(
            manager_config.get("auto_update", {}).get("threshold", 3)
        )

        return Manager(
            name=name,
            scanners=scanners,
            auto_update=auto_update,
            update_threshold=update_threshold,
            db_client=self.vectordb if auto_update else None,
        )

    @staticmethod
    def from_config(config_path: str) -> "Vigil":
        return Vigil(config_path=config_path)


# def setup_vectordb(
#     scanner_conf: dict[str, Any], embedding_conf: dict[str, str]
# ) -> VectorDB:
#     return VectorDB(
#         model=embedding_conf["model"],
#         collection=scanner_conf["collection"],
#         n_results=scanner_conf["n_results"],
#         db_dir=scanner_conf["db_dir"],
#         openai_key=embedding_conf.get("openai_key", os.getenv("OPENAI_API_KEY")),
#     )
