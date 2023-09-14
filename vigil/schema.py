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


class ResponseModel(BaseModel):
    status: str = ''
    timestamp: str = ''
    input_prompt: str = ''
    messages: List[str] = []
    errors: List[str] = []
    results: Dict[str, List[dict]] = {}


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
    label: str = ''
    threshold: float = 0.0


class SimilarityMatch(BaseModel):
    score: float = 0.0
    threshold: float = 0.0
    message: str = ''


class ModerationMatch(BaseModel):
    model_name: str = ''
    category: str = ''
    score: float = 0.0
