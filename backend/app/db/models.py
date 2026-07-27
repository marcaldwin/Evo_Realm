from __future__ import annotations

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.enums import WorldStatus
from .base import Base


class WorldRecord(Base):
    __tablename__ = "worlds"
    __table_args__ = (
        CheckConstraint(
            "current_tick >= 0",
            name="ck_worlds_current_tick_nonnegative",
        ),
        CheckConstraint(
            "status IN ('created', 'running', 'paused')",
            name="ck_worlds_status_valid",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    current_tick: Mapped[int]
    seed: Mapped[int]
    status: Mapped[str] = mapped_column(
        String(20),
        default=WorldStatus.CREATED.value,
        server_default=WorldStatus.CREATED.value,
    )
    locations: Mapped[list[LocationRecord]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
        order_by="LocationRecord.position",
    )
    agents: Mapped[list[AgentRecord]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
        order_by="AgentRecord.position",
    )
    events: Mapped[list[SimulationEventRecord]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
        order_by="SimulationEventRecord.sequence",
    )
    memories: Mapped[list[EpisodicMemoryRecord]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
    )
    social_relationships: Mapped[list[RelationshipRecord]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list[ConversationRecord]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
    )


class LocationRecord(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint(
            "world_database_id",
            "id",
            name="uq_locations_world_id",
        ),
        UniqueConstraint(
            "world_database_id",
            "position",
            name="uq_locations_world_position",
        ),
        CheckConstraint(
            "capacity >= 0",
            name="ck_locations_capacity_nonnegative",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    world_database_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.database_id", ondelete="CASCADE"),
        index=True,
    )
    id: Mapped[str] = mapped_column(String(100))
    position: Mapped[int]
    name: Mapped[str] = mapped_column(String(100))
    location_type: Mapped[str] = mapped_column(String(50))
    x: Mapped[int]
    y: Mapped[int]
    capacity: Mapped[int]
    world: Mapped[WorldRecord] = relationship(back_populates="locations")
    inventory_rows: Mapped[list[LocationInventoryRecord]] = relationship(
        back_populates="location",
        cascade="all, delete-orphan",
    )
    agents: Mapped[list[AgentRecord]] = relationship(
        back_populates="location",
    )


class LocationInventoryRecord(Base):
    __tablename__ = "location_inventory"
    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="ck_location_inventory_quantity_nonnegative",
        ),
    )

    location_database_id: Mapped[int] = mapped_column(
        ForeignKey("locations.database_id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )
    quantity: Mapped[int]
    location: Mapped[LocationRecord] = relationship(
        back_populates="inventory_rows"
    )


class AgentRecord(Base):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint(
            "world_database_id",
            "id",
            name="uq_agents_world_id",
        ),
        UniqueConstraint(
            "world_database_id",
            "position",
            name="uq_agents_world_position",
        ),
        CheckConstraint(
            "hunger BETWEEN 0 AND 100",
            name="ck_agents_hunger_range",
        ),
        CheckConstraint(
            "energy BETWEEN 0 AND 100",
            name="ck_agents_energy_range",
        ),
        CheckConstraint(
            "health BETWEEN 0 AND 100",
            name="ck_agents_health_range",
        ),
        CheckConstraint(
            "money >= 0",
            name="ck_agents_money_nonnegative",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    world_database_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.database_id", ondelete="CASCADE"),
        index=True,
    )
    location_database_id: Mapped[int] = mapped_column(
        ForeignKey("locations.database_id"),
        index=True,
    )
    id: Mapped[str] = mapped_column(String(100))
    position: Mapped[int]
    name: Mapped[str] = mapped_column(String(100))
    occupation: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50))
    hunger: Mapped[int]
    energy: Mapped[int]
    health: Mapped[int]
    money: Mapped[int]
    world: Mapped[WorldRecord] = relationship(back_populates="agents")
    location: Mapped[LocationRecord] = relationship(back_populates="agents")
    inventory_rows: Mapped[list[AgentInventoryRecord]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    memories: Mapped[list[EpisodicMemoryRecord]] = relationship(
        back_populates="owner_agent",
        cascade="all, delete-orphan",
    )
    outgoing_relationships: Mapped[list[RelationshipRecord]] = relationship(
        back_populates="source_agent",
        foreign_keys="RelationshipRecord.source_agent_database_id",
    )
    incoming_relationships: Mapped[list[RelationshipRecord]] = relationship(
        back_populates="target_agent",
        foreign_keys="RelationshipRecord.target_agent_database_id",
    )
    initiated_conversations: Mapped[list[ConversationRecord]] = relationship(
        back_populates="initiator_agent",
        foreign_keys="ConversationRecord.initiator_agent_database_id",
    )
    received_conversations: Mapped[list[ConversationRecord]] = relationship(
        back_populates="participant_agent",
        foreign_keys="ConversationRecord.participant_agent_database_id",
    )


class AgentInventoryRecord(Base):
    __tablename__ = "agent_inventory"
    __table_args__ = (
        CheckConstraint(
            "quantity >= 0",
            name="ck_agent_inventory_quantity_nonnegative",
        ),
    )

    agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )
    quantity: Mapped[int]
    agent: Mapped[AgentRecord] = relationship(
        back_populates="inventory_rows"
    )


class SimulationEventRecord(Base):
    __tablename__ = "simulation_events"
    __table_args__ = (
        UniqueConstraint(
            "world_database_id",
            "sequence",
            name="uq_simulation_events_world_sequence",
        ),
        CheckConstraint(
            "tick >= 0",
            name="ck_simulation_events_tick_nonnegative",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    world_database_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.database_id", ondelete="CASCADE"),
        index=True,
    )
    sequence: Mapped[int]
    tick: Mapped[int]
    event_type: Mapped[str] = mapped_column(String(100))
    agent_id: Mapped[str] = mapped_column(String(100))
    location_id: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str]
    world: Mapped[WorldRecord] = relationship(back_populates="events")
    memories: Mapped[list[EpisodicMemoryRecord]] = relationship(
        back_populates="source_event",
        cascade="all, delete-orphan",
    )


class EpisodicMemoryRecord(Base):
    __tablename__ = "episodic_memories"
    __table_args__ = (
        UniqueConstraint(
            "owner_agent_database_id",
            "source_event_database_id",
            name="uq_episodic_memories_owner_source_event",
        ),
        CheckConstraint(
            "importance BETWEEN 0 AND 1",
            name="ck_episodic_memories_importance_range",
        ),
        CheckConstraint(
            "emotional_value BETWEEN -1 AND 1",
            name="ck_episodic_memories_emotional_value_range",
        ),
        CheckConstraint(
            "creation_tick >= 0",
            name="ck_episodic_memories_creation_tick_nonnegative",
        ),
        CheckConstraint(
            "embedding_dimensions > 0",
            name="ck_episodic_memories_embedding_dimensions_positive",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    world_database_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.database_id", ondelete="CASCADE"),
        index=True,
    )
    owner_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    source_event_database_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_events.database_id", ondelete="CASCADE"),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float)
    emotional_value: Mapped[float] = mapped_column(Float)
    creation_tick: Mapped[int]
    embedding: Mapped[list[float]] = mapped_column(VECTOR())
    embedding_model: Mapped[str] = mapped_column(String(100))
    embedding_dimensions: Mapped[int]
    world: Mapped[WorldRecord] = relationship(back_populates="memories")
    owner_agent: Mapped[AgentRecord] = relationship(
        back_populates="memories"
    )
    source_event: Mapped[SimulationEventRecord] = relationship(
        back_populates="memories"
    )


class RelationshipRecord(Base):
    __tablename__ = "agent_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_agent_database_id",
            "target_agent_database_id",
            name="uq_agent_relationships_direction",
        ),
        CheckConstraint(
            "source_agent_database_id <> target_agent_database_id",
            name="ck_agent_relationships_distinct_agents",
        ),
        CheckConstraint(
            "trust BETWEEN -100 AND 100",
            name="ck_agent_relationships_trust_range",
        ),
        CheckConstraint(
            "affection BETWEEN -100 AND 100",
            name="ck_agent_relationships_affection_range",
        ),
        CheckConstraint(
            "respect BETWEEN -100 AND 100",
            name="ck_agent_relationships_respect_range",
        ),
        CheckConstraint(
            "interaction_count >= 0",
            name="ck_agent_relationships_interactions_nonnegative",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    world_database_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.database_id", ondelete="CASCADE"),
        index=True,
    )
    source_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    target_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    trust: Mapped[int] = mapped_column(default=0, server_default="0")
    affection: Mapped[int] = mapped_column(default=0, server_default="0")
    respect: Mapped[int] = mapped_column(default=0, server_default="0")
    interaction_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
    )
    world: Mapped[WorldRecord] = relationship(
        back_populates="social_relationships"
    )
    source_agent: Mapped[AgentRecord] = relationship(
        back_populates="outgoing_relationships",
        foreign_keys=[source_agent_database_id],
    )
    target_agent: Mapped[AgentRecord] = relationship(
        back_populates="incoming_relationships",
        foreign_keys=[target_agent_database_id],
    )


class ConversationRecord(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "initiator_agent_database_id <> participant_agent_database_id",
            name="ck_conversations_distinct_agents",
        ),
        CheckConstraint(
            "status IN ('active', 'completed')",
            name="ck_conversations_status_valid",
        ),
        CheckConstraint(
            "start_tick >= 0",
            name="ck_conversations_start_tick_nonnegative",
        ),
        CheckConstraint(
            "end_tick IS NULL OR end_tick >= start_tick",
            name="ck_conversations_end_tick_valid",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    world_database_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.database_id", ondelete="CASCADE"),
        index=True,
    )
    initiator_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    participant_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20))
    start_tick: Mapped[int]
    end_tick: Mapped[int | None]
    world: Mapped[WorldRecord] = relationship(back_populates="conversations")
    initiator_agent: Mapped[AgentRecord] = relationship(
        back_populates="initiated_conversations",
        foreign_keys=[initiator_agent_database_id],
    )
    participant_agent: Mapped[AgentRecord] = relationship(
        back_populates="received_conversations",
        foreign_keys=[participant_agent_database_id],
    )
    turns: Mapped[list[ConversationTurnRecord]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationTurnRecord.turn_number",
    )
    outcomes: Mapped[list[ConversationOutcomeRecord]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationOutcomeRecord.database_id",
    )


class ConversationTurnRecord(Base):
    __tablename__ = "conversation_turns"
    __table_args__ = (
        UniqueConstraint(
            "conversation_database_id",
            "turn_number",
            name="uq_conversation_turns_number",
        ),
        CheckConstraint(
            "turn_number BETWEEN 1 AND 4",
            name="ck_conversation_turns_number_range",
        ),
        CheckConstraint(
            "speaker_agent_database_id <> listener_agent_database_id",
            name="ck_conversation_turns_distinct_agents",
        ),
        CheckConstraint(
            "creation_tick >= 0",
            name="ck_conversation_turns_tick_nonnegative",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    conversation_database_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.database_id", ondelete="CASCADE"),
        index=True,
    )
    turn_number: Mapped[int]
    speaker_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    listener_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    dialogue_act: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    creation_tick: Mapped[int]
    conversation: Mapped[ConversationRecord] = relationship(
        back_populates="turns"
    )


class ConversationOutcomeRecord(Base):
    __tablename__ = "conversation_outcomes"
    __table_args__ = (
        CheckConstraint(
            "actor_agent_database_id <> target_agent_database_id",
            name="ck_conversation_outcomes_distinct_agents",
        ),
        CheckConstraint(
            "confirmation_tick >= 0",
            name="ck_conversation_outcomes_tick_nonnegative",
        ),
        CheckConstraint(
            "NOT relationship_applied OR confirmed",
            name="ck_conversation_outcomes_applied_requires_confirmed",
        ),
    )

    database_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    conversation_database_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.database_id", ondelete="CASCADE"),
        index=True,
    )
    outcome_type: Mapped[str] = mapped_column(String(50))
    actor_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    target_agent_database_id: Mapped[int] = mapped_column(
        ForeignKey("agents.database_id", ondelete="CASCADE"),
        index=True,
    )
    confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    confirmation_tick: Mapped[int]
    details: Mapped[dict[str, str | int | bool]] = mapped_column(
        JSON,
        default=dict,
    )
    relationship_applied: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    conversation: Mapped[ConversationRecord] = relationship(
        back_populates="outcomes"
    )
