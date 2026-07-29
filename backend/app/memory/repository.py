from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db.models import (
    AgentRecord,
    EpisodicMemoryRecord,
    MemoryRetrievalItemRecord,
    MemoryRetrievalRecord,
    SimulationEventRecord,
    WorldRecord,
)
from .schemas import EpisodicMemory, MemoryRetrievalResult, RetrievedMemory


@dataclass(frozen=True)
class SourceEventData:
    world_database_id: int
    owner_agent_database_id: int
    source_event_database_id: int
    content: str
    event_tick: int
    source_event_sequence: int
    source_agent_id: str


@dataclass(frozen=True)
class MemoryCandidateData:
    memory: EpisodicMemory
    cosine_distance: float


class MemoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_source_event(
        self,
        world_id: str,
        owner_agent_id: str,
        source_event_sequence: int,
    ) -> SourceEventData | None:
        statement = (
            select(
                WorldRecord.database_id,
                AgentRecord.database_id,
                SimulationEventRecord.database_id,
                SimulationEventRecord.summary,
                SimulationEventRecord.tick,
                SimulationEventRecord.sequence,
                SimulationEventRecord.agent_id,
            )
            .join(
                AgentRecord,
                AgentRecord.world_database_id
                == WorldRecord.database_id,
            )
            .join(
                SimulationEventRecord,
                SimulationEventRecord.world_database_id
                == WorldRecord.database_id,
            )
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == owner_agent_id,
                SimulationEventRecord.sequence
                == source_event_sequence,
            )
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        return SourceEventData(
            world_database_id=row[0],
            owner_agent_database_id=row[1],
            source_event_database_id=row[2],
            content=row[3],
            event_tick=row[4],
            source_event_sequence=row[5],
            source_agent_id=row[6],
        )

    def get_by_source(
        self,
        world_id: str,
        owner_agent_id: str,
        source_event_sequence: int,
    ) -> EpisodicMemory | None:
        statement = (
            select(
                EpisodicMemoryRecord,
                SimulationEventRecord.sequence,
                SimulationEventRecord.agent_id,
                WorldRecord.id,
                AgentRecord.id,
            )
            .join(
                WorldRecord,
                EpisodicMemoryRecord.world_database_id
                == WorldRecord.database_id,
            )
            .join(
                AgentRecord,
                EpisodicMemoryRecord.owner_agent_database_id
                == AgentRecord.database_id,
            )
            .join(
                SimulationEventRecord,
                EpisodicMemoryRecord.source_event_database_id
                == SimulationEventRecord.database_id,
            )
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == owner_agent_id,
                SimulationEventRecord.sequence
                == source_event_sequence,
            )
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        return self._to_memory(
            record=row[0],
            source_event_sequence=row[1],
            source_agent_id=row[2],
            world_id=row[3],
            owner_agent_id=row[4],
        )

    def add(
        self,
        *,
        memory_id: str,
        source: SourceEventData,
        world_id: str,
        owner_agent_id: str,
        importance: float,
        emotional_value: float,
        creation_tick: int,
        embedding: tuple[float, ...],
        embedding_model: str,
    ) -> EpisodicMemory:
        record = EpisodicMemoryRecord(
            id=memory_id,
            world_database_id=source.world_database_id,
            owner_agent_database_id=source.owner_agent_database_id,
            source_event_database_id=source.source_event_database_id,
            content=source.content,
            importance=importance,
            emotional_value=emotional_value,
            creation_tick=creation_tick,
            embedding=list(embedding),
            embedding_model=embedding_model,
            embedding_dimensions=len(embedding),
        )
        self.session.add(record)
        self.session.flush()
        return self._to_memory(
            record=record,
            source_event_sequence=source.source_event_sequence,
            source_agent_id=source.source_agent_id,
            world_id=world_id,
            owner_agent_id=owner_agent_id,
        )

    def find_candidates(
        self,
        *,
        world_id: str,
        owner_agent_id: str,
        query_embedding: tuple[float, ...],
        embedding_model: str,
        candidate_limit: int,
    ) -> list[MemoryCandidateData]:
        distance = EpisodicMemoryRecord.embedding.cosine_distance(
            list(query_embedding)
        )
        statement = (
            select(
                EpisodicMemoryRecord,
                SimulationEventRecord.sequence,
                SimulationEventRecord.agent_id,
                WorldRecord.id,
                AgentRecord.id,
                distance.label("cosine_distance"),
            )
            .join(
                WorldRecord,
                EpisodicMemoryRecord.world_database_id
                == WorldRecord.database_id,
            )
            .join(
                AgentRecord,
                EpisodicMemoryRecord.owner_agent_database_id
                == AgentRecord.database_id,
            )
            .join(
                SimulationEventRecord,
                EpisodicMemoryRecord.source_event_database_id
                == SimulationEventRecord.database_id,
            )
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == owner_agent_id,
                EpisodicMemoryRecord.embedding_model
                == embedding_model,
                EpisodicMemoryRecord.embedding_dimensions
                == len(query_embedding),
            )
            .order_by(distance, EpisodicMemoryRecord.database_id)
            .limit(candidate_limit)
        )
        return [
            MemoryCandidateData(
                memory=self._to_memory(
                    record=row[0],
                    source_event_sequence=row[1],
                    source_agent_id=row[2],
                    world_id=row[3],
                    owner_agent_id=row[4],
                ),
                cosine_distance=float(row[5]),
            )
            for row in self.session.execute(statement)
        ]

    def record_retrieval(
        self,
        *,
        world_id: str,
        result: MemoryRetrievalResult,
    ) -> None:
        agent = self.session.scalar(
            select(AgentRecord)
            .join(WorldRecord)
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == result.owner_agent_id,
            )
        )
        if agent is None:
            raise LookupError("Memory retrieval owner does not exist.")

        memory_ids = [
            memory.memory_id
            for memory in result.memories
        ]
        records_by_id = {
            record.id: record
            for record in self.session.scalars(
                select(EpisodicMemoryRecord).where(
                    EpisodicMemoryRecord.owner_agent_database_id
                    == agent.database_id,
                    EpisodicMemoryRecord.id.in_(memory_ids),
                )
            )
        }
        if set(records_by_id) != set(memory_ids):
            raise LookupError("A retrieved memory does not exist.")

        retrieval = MemoryRetrievalRecord(
            id=result.retrieval_id,
            world_database_id=agent.world_database_id,
            owner_agent_database_id=agent.database_id,
            query_text=result.query_text,
            current_tick=result.current_tick,
            mode=result.mode.value,
        )
        retrieval.items.extend(
            MemoryRetrievalItemRecord(
                memory=records_by_id[memory.memory_id],
                position=position,
                semantic_similarity=memory.semantic_similarity,
                importance_score=memory.importance_score,
                recency_score=memory.recency_score,
                relationship_relevance=memory.relationship_relevance,
                total_score=memory.total_score,
            )
            for position, memory in enumerate(result.memories)
        )
        self.session.add(retrieval)
        self.session.flush()

    def list_latest_retrieved_memories(
        self,
        *,
        world_id: str,
        owner_agent_id: str,
    ) -> list[RetrievedMemory]:
        statement = (
            select(MemoryRetrievalRecord)
            .join(
                WorldRecord,
                MemoryRetrievalRecord.world_database_id
                == WorldRecord.database_id,
            )
            .join(
                AgentRecord,
                MemoryRetrievalRecord.owner_agent_database_id
                == AgentRecord.database_id,
            )
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == owner_agent_id,
            )
            .options(
                selectinload(MemoryRetrievalRecord.items)
                .selectinload(MemoryRetrievalItemRecord.memory)
                .selectinload(EpisodicMemoryRecord.source_event)
            )
            .order_by(MemoryRetrievalRecord.database_id.desc())
            .limit(1)
        )
        retrieval = self.session.scalar(statement)
        if retrieval is None:
            return []

        return [
            RetrievedMemory(
                memory_id=item.memory.id,
                content=item.memory.content,
                importance=item.memory.importance,
                emotional_value=item.memory.emotional_value,
                creation_tick=item.memory.creation_tick,
                source_event_sequence=item.memory.source_event.sequence,
                source_agent_id=item.memory.source_event.agent_id,
                semantic_similarity=item.semantic_similarity,
                importance_score=item.importance_score,
                recency_score=item.recency_score,
                relationship_relevance=item.relationship_relevance,
                total_score=item.total_score,
            )
            for item in retrieval.items
        ]

    @staticmethod
    def _to_memory(
        *,
        record: EpisodicMemoryRecord,
        source_event_sequence: int,
        source_agent_id: str,
        world_id: str,
        owner_agent_id: str,
    ) -> EpisodicMemory:
        return EpisodicMemory(
            memory_id=record.id,
            world_id=world_id,
            owner_agent_id=owner_agent_id,
            content=record.content,
            importance=record.importance,
            emotional_value=record.emotional_value,
            creation_tick=record.creation_tick,
            source_event_sequence=source_event_sequence,
            source_agent_id=source_agent_id,
            embedding=tuple(
                float(value)
                for value in record.embedding
            ),
            embedding_model=record.embedding_model,
            embedding_dimensions=record.embedding_dimensions,
        )
