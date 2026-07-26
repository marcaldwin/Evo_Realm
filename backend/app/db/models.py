from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
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
