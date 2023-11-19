import os

from loguru import logger

from typing import List, Dict, Optional, Callable

from vigil.dispatch import Manager
from vigil.schema import BaseScanner

from vigil.core.config import Config
from vigil.core.canary import CanaryTokens
from vigil.core.vectordb import VectorDB

from vigil.scanners.yara import YaraScanner
from vigil.scanners.vectordb import VectorScanner
from vigil.scanners.transformer import TransformerScanner
from vigil.scanners.similarity import SimilarityScanner
from vigil.scanners.sentiment import SentimentScanner


class Vigil:
    vectordb: Optional[VectorDB] = None

    def __init__(self, config_path: str):
        self.input_scanner: Optional[Manager] = None
        self.output_scanner: Optional[Manager] = None
        self.canary_tokens = CanaryTokens()

        self.config = Config(config_path)
        self._input_scanners: List[BaseScanner] = []
        self._output_scanners: List[BaseScanner] = []
        self._setup_from_config()

    @classmethod
    def _set_vectordb(cls, vectordb_instance):
        cls.vectordb = vectordb_instance

    def _setup_from_config(self):
        self._input_scanners = self._setup_scanners(
            self.config.get_scanner_names('input_scanners')
        )
        self._output_scanners = self._setup_scanners(
            self.config.get_scanner_names('output_scanners')
        )
        self.input_scanner = self._create_manager('input_scanners', self._input_scanners)
        self.output_scanner = self._create_manager('output_scanners', self._output_scanners)

    def _setup_scanners(self, scanner_names: List[str]) -> List[BaseScanner]:
        scanners = []

        for name in scanner_names:
            setup_fn = SCANNER_SETUPS.get(name)
            if not setup_fn:
                raise ValueError(f'Unsupported scanner set in config: {name}')

            scanner_config = self.config.get_scanner_config(name)
            if name == 'vectordb' or name == 'similarity':
                embedding_conf = self.config.get_general_config().get('embedding', {})
                scanner = setup_fn(scanner_config, embedding_conf)
            else:
                scanner = setup_fn(scanner_config)
            scanners.append(scanner)

        return scanners

    def _create_manager(self, name: str, scanners: List[BaseScanner]) -> Manager:
        manager_config = self.config.get_general_config() if self.config else {}
        auto_update = manager_config.get('embedding', {}).get('auto_update', False)
        update_threshold = int(manager_config.get('embedding', {}).get('update_threshold', 3))

        return Manager(
            name=name,
            scanners=scanners,
            auto_update=auto_update,
            update_threshold=update_threshold,
            db_client=self.vectordb if auto_update else None
        )

    @staticmethod
    def from_config(config_path: str) -> 'Vigil':
        return Vigil(config_path=config_path)


def setup_yara_scanner(conf) -> BaseScanner:
    yara_dir = conf['rules_dir']
    if yara_dir is None:
        logger.error('No yara rules directory set in config')
        raise ValueError('No yara rules directory set in config')

    yara_scanner = YaraScanner(rules_dir=yara_dir)
    yara_scanner.load_rules()
    return yara_scanner


def setup_sentiment_scanner(conf) -> BaseScanner:
    threshold = float(conf['threshold'])
    return SentimentScanner(threshold=threshold)


def setup_vectordb(scanner_conf, embedding_conf) -> BaseScanner:
    vdb_dir = scanner_conf['db_dir']
    vdb_collection = scanner_conf['collection']
    vdb_threshold = scanner_conf['threshold']
    vdb_n_results = scanner_conf['n_results']

    if not os.path.isdir(vdb_dir):
        logger.error(f'VectorDB directory not found: {vdb_dir}')
        raise ValueError(f'VectorDB directory not found: {vdb_dir}')

    emb_model = embedding_conf['model']
    if emb_model is None:
        logger.error('No embedding model set in config file')
        raise ValueError('No embedding model set in config file')

    if emb_model == 'openai':
        openai_key = embedding_conf['openai_api_key']
        openai_model = embedding_conf['openai_model']

        if openai_key is None or openai_model is None:
            logger.error('OpenAI embedding model selected but no key or model name set in config')
            raise ValueError('OpenAI embedding model selected but no key or model name set in config')

        vectordb = VectorDB(
                embed_model='openai',
                collection_name=vdb_collection,
                db_dir=vdb_dir,
                n_results=int(vdb_n_results),
                openai_key=openai_key,
                openai_model=openai_model
            )

    else:
        vectordb = VectorDB(
                embed_model=emb_model,
                collection_name=vdb_collection,
                db_dir=vdb_dir,
                n_results=int(vdb_n_results)
            )
    
    return vectordb


def setup_vectordb_scanner(scanner_conf, embedding_conf) -> BaseScanner:
    vectordb = setup_vectordb(scanner_conf, embedding_conf)

    Vigil._set_vectordb(vectordb)

    return VectorScanner(
        db_client=vectordb,
        threshold=float(scanner_conf['threshold'])
    )


def setup_similarity_scanner(scanner_conf, embedding_conf) -> BaseScanner:
    sim_threshold = scanner_conf['threshold']
    emb_model = embedding_conf['model']

    if not sim_threshold or not emb_model:
        logger.error('Missing configurations for Similarity Scanner')
        raise ValueError('Missing configurations for Similarity Scanner')

    openai_key = None
    if emb_model == 'openai':
        openai_key = embedding_conf['openai_api_key']

    return SimilarityScanner(
        model=emb_model,
        threshold=float(sim_threshold),
        openai_key=openai_key
    )


def setup_transformer_scanner(conf) -> BaseScanner:
    lm_name = conf['model']
    threshold = conf['threshold']

    if not lm_name or not threshold:
        logger.error('Missing configurations for Transformer Scanner')
        raise ValueError('Missing configurations for Transformer Scanner')

    return TransformerScanner(
        model=lm_name,
        threshold=float(threshold)
    )


SCANNER_SETUPS: Dict[str, Callable] = {
    'yara': setup_yara_scanner,
    'sentiment': setup_sentiment_scanner,
    'vectordb': setup_vectordb_scanner,
    'similarity': setup_similarity_scanner,
    'transformer': setup_transformer_scanner
}
