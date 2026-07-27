from collections.abc import Mapping
from math import isfinite
from uuid import uuid4

from ..core.enums import MemoryMode
from .embedding import EmbeddingClient, EmbeddingResult
from .repository import MemoryCandidateData, MemoryRepository
from .schemas import (
    EpisodicMemory,
    MemoryRetrievalResult,
    RetrievedMemory,
)


SEMANTIC_WEIGHT = 0.5
IMPORTANCE_WEIGHT = 0.2
RECENCY_WEIGHT = 0.2
RELATIONSHIP_WEIGHT = 0.1
RECENCY_HALF_LIFE_TICKS = 50
MAX_RETRIEVED_MEMORIES = 5


class EpisodicMemoryService:
    def __init__(
        self,
        mode: MemoryMode,
        *,
        repository: MemoryRepository | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        if mode == MemoryMode.VECTOR_EPISODIC:
            if repository is None or embedding_client is None:
                raise ValueError(
                    "Vector memory requires a repository and "
                    "embedding client."
                )
        self.mode = mode
        self.repository = repository
        self.embedding_client = embedding_client

    def create_from_event(
        self,
        *,
        world_id: str,
        owner_agent_id: str,
        source_event_sequence: int,
        importance: float,
        emotional_value: float,
        creation_tick: int,
    ) -> EpisodicMemory | None:
        if self.mode == MemoryMode.NO_MEMORY:
            return None

        repository, embedding_client = self._vector_dependencies()
        existing = repository.get_by_source(
            world_id,
            owner_agent_id,
            source_event_sequence,
        )
        if existing is not None:
            return existing

        source = repository.get_source_event(
            world_id,
            owner_agent_id,
            source_event_sequence,
        )
        if source is None:
            raise LookupError(
                "Memory owner or source event does not exist."
            )
        if creation_tick < source.event_tick:
            raise ValueError(
                "Memory cannot be created before its source event."
            )
        if not 0 <= importance <= 1:
            raise ValueError("Memory importance must be between 0 and 1.")
        if not -1 <= emotional_value <= 1:
            raise ValueError(
                "Memory emotional value must be between -1 and 1."
            )

        embedding = self._embed(embedding_client, source.content)
        return repository.add(
            memory_id=str(uuid4()),
            source=source,
            world_id=world_id,
            owner_agent_id=owner_agent_id,
            importance=importance,
            emotional_value=emotional_value,
            creation_tick=creation_tick,
            embedding=embedding.vector,
            embedding_model=embedding.model,
        )

    def retrieve(
        self,
        *,
        world_id: str,
        owner_agent_id: str,
        query_text: str,
        current_tick: int,
        relationship_scores: Mapping[str, int] | None = None,
        limit: int = MAX_RETRIEVED_MEMORIES,
    ) -> MemoryRetrievalResult:
        normalized_query = query_text.strip()
        if not normalized_query:
            raise ValueError("Memory query cannot be empty.")
        if len(normalized_query) > 4000:
            raise ValueError(
                "Memory query cannot exceed 4000 characters."
            )
        if current_tick < 0:
            raise ValueError("Current tick cannot be negative.")
        if limit <= 0:
            raise ValueError("Memory retrieval limit must be positive.")

        retrieval_limit = min(limit, MAX_RETRIEVED_MEMORIES)
        if self.mode == MemoryMode.NO_MEMORY:
            return MemoryRetrievalResult(
                retrieval_id=str(uuid4()),
                mode=self.mode,
                owner_agent_id=owner_agent_id,
                query_text=normalized_query,
                current_tick=current_tick,
            )

        repository, embedding_client = self._vector_dependencies()
        query_embedding = self._embed(
            embedding_client,
            normalized_query,
        )
        candidates = repository.find_candidates(
            world_id=world_id,
            owner_agent_id=owner_agent_id,
            query_embedding=query_embedding.vector,
            embedding_model=query_embedding.model,
            candidate_limit=max(20, retrieval_limit * 10),
        )
        scored_memories = [
            self._score_candidate(
                candidate,
                current_tick=current_tick,
                relationship_scores=relationship_scores or {},
            )
            for candidate in candidates
        ]
        scored_memories.sort(
            key=lambda memory: (
                -memory.total_score,
                -memory.semantic_similarity,
                -memory.creation_tick,
                memory.memory_id,
            )
        )
        return MemoryRetrievalResult(
            retrieval_id=str(uuid4()),
            mode=self.mode,
            owner_agent_id=owner_agent_id,
            query_text=normalized_query,
            current_tick=current_tick,
            memories=scored_memories[:retrieval_limit],
        )

    def _vector_dependencies(
        self,
    ) -> tuple[MemoryRepository, EmbeddingClient]:
        if self.repository is None or self.embedding_client is None:
            raise RuntimeError(
                "Vector memory dependencies are unavailable."
            )
        return self.repository, self.embedding_client

    @staticmethod
    def _embed(
        embedding_client: EmbeddingClient,
        text: str,
    ) -> EmbeddingResult:
        result = embedding_client.embed(text)
        if not result.model.strip():
            raise ValueError("Embedding model cannot be empty.")
        if embedding_client.dimensions <= 0:
            raise ValueError(
                "Embedding dimensions must be positive."
            )
        if len(result.vector) != embedding_client.dimensions:
            raise ValueError(
                "Embedding length does not match client dimensions."
            )
        if not all(isfinite(value) for value in result.vector):
            raise ValueError(
                "Embedding values must be finite numbers."
            )
        if not any(value != 0 for value in result.vector):
            raise ValueError(
                "Embedding vector cannot contain only zeros."
            )
        return result

    @staticmethod
    def _score_candidate(
        candidate: MemoryCandidateData,
        *,
        current_tick: int,
        relationship_scores: Mapping[str, int],
    ) -> RetrievedMemory:
        memory = candidate.memory
        semantic_similarity = max(
            0.0,
            min(1.0, 1.0 - candidate.cosine_distance),
        )
        age = max(0, current_tick - memory.creation_tick)
        recency_score = 1.0 / (
            1.0 + age / RECENCY_HALF_LIFE_TICKS
        )
        relationship_score = relationship_scores.get(
            memory.source_agent_id,
            0,
        )
        relationship_relevance = min(
            1.0,
            abs(relationship_score) / 100,
        )
        total_score = (
            semantic_similarity * SEMANTIC_WEIGHT
            + memory.importance * IMPORTANCE_WEIGHT
            + recency_score * RECENCY_WEIGHT
            + relationship_relevance * RELATIONSHIP_WEIGHT
        )
        return RetrievedMemory(
            memory_id=memory.memory_id,
            content=memory.content,
            importance=memory.importance,
            emotional_value=memory.emotional_value,
            creation_tick=memory.creation_tick,
            source_event_sequence=memory.source_event_sequence,
            source_agent_id=memory.source_agent_id,
            semantic_similarity=semantic_similarity,
            importance_score=memory.importance,
            recency_score=recency_score,
            relationship_relevance=relationship_relevance,
            total_score=max(0.0, min(1.0, total_score)),
        )
