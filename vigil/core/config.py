import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class EmbeddingConfig(BaseModel):
    """embedding config"""

    # to get around the fact you can't call a field "model"
    model_config = ConfigDict(protected_namespaces=())

    model: str
    openai_key: Optional[SecretStr] = Field(None)

    @field_validator("openai_key", mode="before")
    def optional_openai_key_env(cls, input: Optional[str]) -> Optional[str]:
        if input is None or input.strip() == "":
            logger.debug(
                "OpenAI key not specified in config, loading it from OPENAI_API_KEY environment variable."
            )
            return os.getenv("OPENAI_API_KEY")
        return input


class MainConfig(BaseModel):
    """main program config"""

    use_cache: bool = Field(True)
    cache_max: int = Field(500)


class VectorDBConfig(BaseModel):
    """Vector DB configuragion"""

    # to get around the fact you can't call a field "model"
    model_config = ConfigDict(protected_namespaces=())

    collection: str = Field("data-openai")
    db_dir: Optional[str]
    model: Optional[str] = Field(None)
    # When `n` number of scanners match on a prompt (excluding the sentiment scanner), that prompt will be indexed in the database.
    n_results: int = Field(5)


class AutoUpdateConfig(BaseModel):
    enabled: bool = Field(True)
    threshold: int = Field(3)


class ScannerConfig(BaseModel):
    """individual scanner config"""

    rules_dir: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    threshold: Optional[float] = Field(None)


class ScannersConfig(BaseModel):
    """global scanner config"""

    input_scanners: List[str] = Field([])
    output_scanners: List[str] = Field([])
    # this can be a variety of things
    scanner_config: Dict[str, ScannerConfig] = Field({})

    @field_validator("input_scanners", "output_scanners", mode="before")
    def split_arg(cls, input):
        return input.split(",")


class ConfigFile(BaseModel):
    """this is used for parsing the config file"""

    main: MainConfig
    embedding: EmbeddingConfig
    vectordb: VectorDBConfig
    auto_update: AutoUpdateConfig
    scanners: ScannersConfig

    @classmethod
    def from_config_file(cls, filepath: Optional[Path]) -> "ConfigFile":
        """load from .conf file"""
        if filepath is None:
            if "VIGIL_CONFIG" in os.environ:
                filepath = Path(os.environ["VIGIL_CONFIG"])
            else:
                logger.error(
                    "No config file specified on the command line or VIGIL_CONFIG env var, quitting!"
                )
                raise ValueError("You need to specify a config file path!")
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        config = configparser.ConfigParser()
        config.read_file(filepath.open(mode="r", encoding="utf-8"))
        return cls.from_configparser(config)

    @classmethod
    def from_configparser(cls, config: configparser.ConfigParser) -> "ConfigFile":
        """parse a configParser object and turn it into a ConfigFile object"""
        data: Dict[str, Any] = {}
        for section in config.sections():
            if not section.startswith("scanner:"):
                data[section] = dict(config.items(section))
            else:
                # we're handling the scanner config
                if "scanners" not in data:
                    data["scanners"] = {}
                if "scanner_config" not in data["scanners"]:
                    data["scanners"]["scanner_config"] = {}
                scanner_name = section.split(":")[1]
                data["scanners"]["scanner_config"][scanner_name] = dict(
                    config.items(section)
                )
        return cls(**data)

    def get_scanner_names(self, scanner_type: str) -> List[str]:
        """returns the names of the configured scanners"""
        if hasattr(self.scanners, scanner_type):
            return getattr(self.scanners, scanner_type)
        raise ValueError(
            "scanner_type needs to be one of input_scanners, output_scanners"
        )
