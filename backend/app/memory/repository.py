from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    AgentRecord,
    EpisodicMemoryRecord,
    SimulationEventRecord,
    WorldRecord,
)
from .schemas import EpisodicMemory


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
