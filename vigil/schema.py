from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class DatasetEntry(BaseModel):
    text: str = ''
    embeddings: List[float] = []
    metadata: dict = {'model': 'unknown'}


class ScanModel(BaseModel):
    prompt: str = ''
    prompt_response: str = None
    embedding: List[float] = []
    results: List = []


class ResponseModel(BaseModel):
    status: str = ''
    uuid: UUID = Field(default_factory=uuid4)
    timestamp: str = ''
    prompt: str = ''
    prompt_response: str = None
    prompt_entropy: float = 0.0
    messages: List[str] = []
    errors: List[str] = []
    results: Dict[str, List[dict]] = {}


class BaseScanner(ABC):
    def __init__(self, name: str = '', config_dict: Dict = {}) -> None:
        self.name = name
        self.config = config_dict

    @abstractmethod
    def analyze(self, prompt: str = None, response: str = None, scan_uuid: UUID = uuid4()) -> ScanModel:
        pass


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


class SentimentMatch(BaseModel):
    negative: float = 0.0
    neutral: float = 0.0
    positive: float = 0.0
    compound: float = 0.0
    threshold: float = 0.0
