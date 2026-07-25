"""World creation service."""

from uuid import uuid4

from ..api.schemas.world import WorldCreate
from ..simulation.models import Agent, Location, World


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

    return World(
        id=str(uuid4()),
        name=configuration.name,
        current_tick=configuration.starting_tick,
        seed=configuration.seed,
        locations=locations,
        agents=agents,
    )
