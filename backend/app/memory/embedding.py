from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingResult:
    vector: tuple[float, ...]
    model: str


class EmbeddingProviderError(Exception):
    pass


class EmbeddingClient(Protocol):
    model_name: str
    dimensions: int

    def embed(self, text: str) -> EmbeddingResult:
        ...
