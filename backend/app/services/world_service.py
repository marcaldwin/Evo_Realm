"""In-memory world creation and retrieval service."""

from dataclasses import dataclass
from uuid import uuid4

from ..api.schemas.world import WorldCreate
from ..simulation.engine import advance_tick
from ..simulation.models import (
    Agent,
    Location,
    SimulationEvent,
    World,
)


_worlds_by_id: dict[str, World] = {}


@dataclass(frozen=True)
class WorldSummary:
    id: str
    name: str
    current_tick: int
    seed: int
    agent_count: int


def create_world(configuration: WorldCreate) -> World:
    locations = [
        Location(
            id=location.id,
            name=location.name,
            location_type=location.location_type,
            x=location.x,
            y=location.y,
            capacity=location.capacity,
            inventory=dict(location.inventory),
        )
        for location in configuration.locations
    ]
    agents = [
        Agent(
            id=agent.id,
            name=agent.name,
            occupation=agent.occupation,
            location_id=agent.location_id,
            status=agent.status,
            hunger=agent.hunger,
            energy=agent.energy,
            health=agent.health,
            money=agent.money,
            inventory=dict(agent.inventory),
        )
        for agent in configuration.agents
    ]

    world = World(
        id=str(uuid4()),
        name=configuration.name,
        current_tick=configuration.starting_tick,
        seed=configuration.seed,
        locations=locations,
        agents=agents,
    )
    _worlds_by_id[world.id] = world
    return world


def get_world(world_id: str) -> World | None:
    return _worlds_by_id.get(world_id)


def list_worlds() -> list[WorldSummary]:
    return [
        WorldSummary(
            id=world.id,
            name=world.name,
            current_tick=world.current_tick,
            seed=world.seed,
            agent_count=len(world.agents),
        )
        for world in _worlds_by_id.values()
    ]


def list_world_agents(world_id: str) -> list[Agent] | None:
    world = get_world(world_id)
    if world is None:
        return None
    return list(world.agents)


def list_world_events(world_id: str) -> list[SimulationEvent] | None:
    world = get_world(world_id)
    if world is None:
        return None
    return list(world.events)


def step_world(world_id: str) -> World | None:
    world = get_world(world_id)
    if world is None:
        return None

    updated_world = advance_tick(world)
    _worlds_by_id[world_id] = updated_world
    return updated_world
