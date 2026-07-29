from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..core.enums import (
    AgentStatus,
    EventType,
    LocationType,
    Occupation,
    ResourceType,
    WorldStatus,
)
from ..db.models import (
    AgentInventoryRecord,
    AgentRecord,
    LocationInventoryRecord,
    LocationRecord,
    SimulationEventRecord,
    WorldRecord,
)
from ..simulation.models import (
    Agent,
    Location,
    SimulationEvent,
    World,
)


@dataclass(frozen=True)
class WorldSummaryData:
    id: str
    name: str
    current_tick: int
    seed: int
    status: WorldStatus
    agent_count: int


class WorldRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, world: World) -> None:
        world_record = WorldRecord(
            id=world.id,
            name=world.name,
            current_tick=world.current_tick,
            seed=world.seed,
            status=world.status.value,
        )
        locations_by_id: dict[str, LocationRecord] = {}

        for position, location in enumerate(world.locations):
            location_record = LocationRecord(
                id=location.id,
                position=position,
                name=location.name,
                location_type=location.location_type.value,
                x=location.x,
                y=location.y,
                capacity=location.capacity,
                inventory_rows=[
                    LocationInventoryRecord(
                        resource_type=resource_type.value,
                        quantity=quantity,
                    )
                    for resource_type, quantity in location.inventory.items()
                ],
            )
            world_record.locations.append(location_record)
            locations_by_id[location.id] = location_record

        for position, agent in enumerate(world.agents):
            agent_record = AgentRecord(
                id=agent.id,
                position=position,
                name=agent.name,
                occupation=agent.occupation.value,
                status=agent.status.value,
                hunger=agent.hunger,
                energy=agent.energy,
                health=agent.health,
                money=agent.money,
                personality_traits=dict(agent.personality_traits),
                active_goal=agent.active_goal,
                location=locations_by_id[agent.location_id],
                inventory_rows=[
                    AgentInventoryRecord(
                        resource_type=resource_type.value,
                        quantity=quantity,
                    )
                    for resource_type, quantity in agent.inventory.items()
                ],
            )
            world_record.agents.append(agent_record)

        world_record.events.extend(
            self._event_record(event, sequence)
            for sequence, event in enumerate(world.events)
        )
        self.session.add(world_record)
        self.session.flush()

    def get(
        self,
        world_id: str,
        *,
        for_update: bool = False,
    ) -> World | None:
        world_record = self._get_record(world_id, for_update=for_update)
        if world_record is None:
            return None
        return self._to_world(world_record)

    def list_summaries(self) -> list[WorldSummaryData]:
        statement = (
            select(
                WorldRecord.id,
                WorldRecord.name,
                WorldRecord.current_tick,
                WorldRecord.seed,
                WorldRecord.status,
                func.count(AgentRecord.database_id).label("agent_count"),
            )
            .outerjoin(
                AgentRecord,
                AgentRecord.world_database_id == WorldRecord.database_id,
            )
            .group_by(WorldRecord.database_id)
            .order_by(WorldRecord.database_id)
        )
        return [
            WorldSummaryData(
                id=row.id,
                name=row.name,
                current_tick=row.current_tick,
                seed=row.seed,
                status=WorldStatus(row.status),
                agent_count=row.agent_count,
            )
            for row in self.session.execute(statement)
        ]

    def save(self, world: World) -> None:
        world_record = self._get_record(world.id, for_update=False)
        if world_record is None:
            raise LookupError(f"World {world.id} does not exist.")

        world_record.name = world.name
        world_record.current_tick = world.current_tick
        world_record.seed = world.seed
        world_record.status = world.status.value

        location_records = {
            location.id: location
            for location in world_record.locations
        }
        if set(location_records) != {
            location.id for location in world.locations
        }:
            raise ValueError("World locations cannot change during a step.")

        for position, location in enumerate(world.locations):
            location_record = location_records[location.id]
            location_record.position = position
            location_record.name = location.name
            location_record.location_type = location.location_type.value
            location_record.x = location.x
            location_record.y = location.y
            location_record.capacity = location.capacity
            self._sync_location_inventory(
                location_record,
                location.inventory,
            )

        agent_records = {
            agent.id: agent
            for agent in world_record.agents
        }
        if set(agent_records) != {agent.id for agent in world.agents}:
            raise ValueError("World agents cannot change during a step.")

        for position, agent in enumerate(world.agents):
            agent_record = agent_records[agent.id]
            agent_record.position = position
            agent_record.name = agent.name
            agent_record.occupation = agent.occupation.value
            agent_record.status = agent.status.value
            agent_record.hunger = agent.hunger
            agent_record.energy = agent.energy
            agent_record.health = agent.health
            agent_record.money = agent.money
            agent_record.personality_traits = dict(
                agent.personality_traits
            )
            agent_record.active_goal = agent.active_goal
            agent_record.location = location_records[agent.location_id]
            self._sync_agent_inventory(agent_record, agent.inventory)

        stored_events = [
            self._to_event(event_record)
            for event_record in world_record.events
        ]
        if world.events[: len(stored_events)] != stored_events:
            raise ValueError("Stored simulation events cannot be changed.")

        world_record.events.extend(
            self._event_record(event, sequence)
            for sequence, event in enumerate(
                world.events[len(stored_events) :],
                start=len(stored_events),
            )
        )
        self.session.flush()

    def _get_record(
        self,
        world_id: str,
        *,
        for_update: bool,
    ) -> WorldRecord | None:
        statement = (
            select(WorldRecord)
            .where(WorldRecord.id == world_id)
            .options(
                selectinload(WorldRecord.locations).selectinload(
                    LocationRecord.inventory_rows
                ),
                selectinload(WorldRecord.agents).selectinload(
                    AgentRecord.location
                ),
                selectinload(WorldRecord.agents).selectinload(
                    AgentRecord.inventory_rows
                ),
                selectinload(WorldRecord.events),
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    @staticmethod
    def _sync_location_inventory(
        location_record: LocationRecord,
        inventory: dict[ResourceType, int],
    ) -> None:
        rows = {
            row.resource_type: row
            for row in location_record.inventory_rows
        }
        expected = {
            resource_type.value: quantity
            for resource_type, quantity in inventory.items()
        }
        location_record.inventory_rows[:] = [
            row
            for resource_type, row in rows.items()
            if resource_type in expected
        ]
        for resource_type, quantity in expected.items():
            row = rows.get(resource_type)
            if row is None:
                location_record.inventory_rows.append(
                    LocationInventoryRecord(
                        resource_type=resource_type,
                        quantity=quantity,
                    )
                )
            else:
                row.quantity = quantity

    @staticmethod
    def _sync_agent_inventory(
        agent_record: AgentRecord,
        inventory: dict[ResourceType, int],
    ) -> None:
        rows = {
            row.resource_type: row
            for row in agent_record.inventory_rows
        }
        expected = {
            resource_type.value: quantity
            for resource_type, quantity in inventory.items()
        }
        agent_record.inventory_rows[:] = [
            row
            for resource_type, row in rows.items()
            if resource_type in expected
        ]
        for resource_type, quantity in expected.items():
            row = rows.get(resource_type)
            if row is None:
                agent_record.inventory_rows.append(
                    AgentInventoryRecord(
                        resource_type=resource_type,
                        quantity=quantity,
                    )
                )
            else:
                row.quantity = quantity

    @staticmethod
    def _event_record(
        event: SimulationEvent,
        sequence: int,
    ) -> SimulationEventRecord:
        return SimulationEventRecord(
            sequence=sequence,
            tick=event.tick,
            event_type=event.event_type.value,
            agent_id=event.agent_id,
            location_id=event.location_id,
            summary=event.summary,
        )

    @staticmethod
    def _to_event(event_record: SimulationEventRecord) -> SimulationEvent:
        return SimulationEvent(
            tick=event_record.tick,
            event_type=EventType(event_record.event_type),
            agent_id=event_record.agent_id,
            location_id=event_record.location_id,
            summary=event_record.summary,
        )

    @classmethod
    def _to_world(cls, world_record: WorldRecord) -> World:
        return World(
            id=world_record.id,
            name=world_record.name,
            current_tick=world_record.current_tick,
            seed=world_record.seed,
            status=WorldStatus(world_record.status),
            locations=[
                Location(
                    id=location.id,
                    name=location.name,
                    location_type=LocationType(location.location_type),
                    x=location.x,
                    y=location.y,
                    capacity=location.capacity,
                    inventory={
                        ResourceType(row.resource_type): row.quantity
                        for row in location.inventory_rows
                    },
                )
                for location in world_record.locations
            ],
            agents=[
                Agent(
                    id=agent.id,
                    name=agent.name,
                    occupation=Occupation(agent.occupation),
                    location_id=agent.location.id,
                    status=AgentStatus(agent.status),
                    hunger=agent.hunger,
                    energy=agent.energy,
                    health=agent.health,
                    money=agent.money,
                    inventory={
                        ResourceType(row.resource_type): row.quantity
                        for row in agent.inventory_rows
                    },
                    personality_traits=dict(agent.personality_traits),
                    active_goal=agent.active_goal,
                )
                for agent in world_record.agents
            ],
            events=[
                cls._to_event(event)
                for event in world_record.events
            ],
        )
