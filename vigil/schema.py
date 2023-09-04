from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class BaseScanner(ABC):
    def __init__(self, name: str = '', config_dict: Dict = {}) -> None:
        self.name = name
        self.config = config_dict

    @abstractmethod
    def analyze(self, input):
        pass


class ScanModel(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    input_prompt: str = ''
    embedding: List[float] = []
    results: dict = {}
    metadata: Optional[dict] = {}


class VectorMatch(BaseModel):
    text: str = ''
    metadata: Optional[dict] = {}
    distance: float = 0.0


class YaraMatch(BaseModel):
    rule_name: str = ''
    category: str = ''
    tags: List[str] = []


class ModelMatch(BaseModel):
    model_name: str = ''
    score: float = 0.0
    threshold: float = 0.0


class ModerationMatch(BaseModel):
    model_name: str = ''
    category: float = 0.0
    score: float = 0.0
