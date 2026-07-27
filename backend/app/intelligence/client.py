from dataclasses import dataclass
from typing import Protocol

from .schemas import TokenUsage


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    token_usage: TokenUsage


class LLMProviderError(Exception):
    pass


class LLMTimeoutError(LLMProviderError):
    pass


class LLMClient(Protocol):
    provider_name: str
    model_name: str

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> LLMResponse:
        ...
