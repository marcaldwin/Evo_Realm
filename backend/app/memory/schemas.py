from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..core.enums import MemoryMode


RequiredIdentifier = Annotated[str, Field(min_length=1, max_length=100)]
MemoryContent = Annotated[str, Field(min_length=1, max_length=4000)]
NonNegativeInteger = Annotated[int, Field(ge=0)]
PositiveInteger = Annotated[int, Field(gt=0)]
NormalizedScore = Annotated[float, Field(ge=0, le=1)]
EmotionalValue = Annotated[float, Field(ge=-1, le=1)]


class MemorySchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class EpisodicMemory(MemorySchema):
    memory_id: RequiredIdentifier
    world_id: RequiredIdentifier
    owner_agent_id: RequiredIdentifier
    content: MemoryContent
    importance: NormalizedScore
    emotional_value: EmotionalValue
    creation_tick: NonNegativeInteger
    source_event_sequence: NonNegativeInteger
    source_agent_id: RequiredIdentifier
    embedding: tuple[float, ...]
    embedding_model: RequiredIdentifier
    embedding_dimensions: PositiveInteger

    @model_validator(mode="after")
    def validate_embedding_dimensions(self) -> Self:
        if len(self.embedding) != self.embedding_dimensions:
            raise ValueError(
                "Embedding length must match embedding dimensions."
            )
        return self


class RetrievedMemory(MemorySchema):
    memory_id: RequiredIdentifier
    content: MemoryContent
    importance: NormalizedScore
    emotional_value: EmotionalValue
    creation_tick: NonNegativeInteger
    source_event_sequence: NonNegativeInteger
    source_agent_id: RequiredIdentifier
    semantic_similarity: NormalizedScore
    importance_score: NormalizedScore
    recency_score: NormalizedScore
    relationship_relevance: NormalizedScore
    total_score: NormalizedScore


class MemoryRetrievalResult(MemorySchema):
    retrieval_id: RequiredIdentifier
    mode: MemoryMode
    owner_agent_id: RequiredIdentifier
    query_text: MemoryContent
    current_tick: NonNegativeInteger
    memories: list[RetrievedMemory] = Field(
        default_factory=list,
        max_length=5,
    )

    @model_validator(mode="after")
    def validate_no_memory_mode(self) -> Self:
        if self.mode == MemoryMode.NO_MEMORY and self.memories:
            raise ValueError(
                "No-memory mode cannot return persistent memories."
            )
        return self
