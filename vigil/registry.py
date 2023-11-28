# from functools import wraps
# from abc import ABC, abstractmethod
from typing import Dict, List, Type, Callable, Optional

from vigil.schema import BaseScanner


class Registration:
    @staticmethod
    def scanner(
        name: str, requires_config=False, requires_vectordb=False, **additional_metadata
    ):
        def decorator(scanner_class: Type[BaseScanner]):
            ScannerRegistry.register_scanner(
                name,
                scanner_class,
                requires_config,
                requires_vectordb,
                **additional_metadata,
            )
            return scanner_class

        return decorator


class ScannerRegistry:
    _registry: Dict[str, dict] = {}

    @classmethod
    def register_scanner(
        cls,
        name: str,
        scanner_class: Type[BaseScanner],
        requires_config=False,
        requires_vectordb=False,
        requires_embedding=False,
        **metadata,
    ):
        cls._registry[name] = {
            "class": scanner_class,
            "requires_config": requires_config,
            "requires_vectordb": requires_vectordb,
            "requires_embedding": requires_embedding,
            **metadata,
        }

    @classmethod
    def create_scanner(
        cls,
        name: str,
        config: Optional[dict] = None,
        vectordb: Optional[Callable] = None,
        embedder: Optional[Callable] = None,
        **params,
    ) -> BaseScanner:
        if name not in cls._registry:
            raise ValueError(f"No scanner registered with name: {name}")

        scanner_info = cls._registry[name]
        scanner_class = scanner_info["class"]

        init_params = {}
        if scanner_info["requires_config"]:
            if config is None:
                raise ValueError(f"Config required for scanner '{name}'")
            init_params = config

        if scanner_info["requires_vectordb"]:
            if vectordb is None:
                raise ValueError(f"VectorDB required for scanner '{name}'")

            init_params.update({"db_client": vectordb})

        if scanner_info["requires_embedding"]:
            if embedder is None:
                raise ValueError(f"Embedder required for scanner '{name}'")

            init_params.update({"embedder": embedder})

        scanner_cls = scanner_class(**init_params)
        if hasattr(scanner_cls, "post_init"):
            scanner_cls.post_init()

        return scanner_cls

    @classmethod
    def get_scanner_names(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    def get_scanner_cls(cls) -> List[Type[BaseScanner]]:
        return [info["class"] for info in cls._registry.values()]

    @classmethod
    def get_scanner_metadata(cls, name: str):
        if name not in cls._registry:
            raise ValueError(f"No scanner registered with name: {name}")
        return cls._registry[name]
