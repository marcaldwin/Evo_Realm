from collections.abc import Sequence

from ..memory.schemas import RetrievedMemory
from ..simulation.models import Agent, Location, World
from .schemas import (
    AgentDecisionState,
    AvailableAction,
    DecisionContext,
    GoalSummary,
    NearbyEntitySummary,
    RelationshipSummary,
)


def build_agent_decision_state(
    agent: Agent,
) -> AgentDecisionState:
    return AgentDecisionState(
        agent_id=agent.id,
        name=agent.name,
        occupation=agent.occupation,
        status=agent.status,
        location_id=agent.location_id,
        hunger=agent.hunger,
        energy=agent.energy,
        health=agent.health,
        money=agent.money,
        inventory=dict(agent.inventory),
    )


def location_distance(
    first: Location,
    second: Location,
) -> int:
    return abs(first.x - second.x) + abs(first.y - second.y)


def build_nearby_locations(
    world: World,
    agent: Agent,
    *,
    max_distance: int = 5,
) -> list[NearbyEntitySummary]:
    if max_distance < 0:
        raise ValueError("Maximum distance cannot be negative.")

    locations_by_id = {
        location.id: location
        for location in world.locations
    }
    current_location = locations_by_id.get(agent.location_id)
    if current_location is None:
        raise ValueError("Agent references an unknown location.")

    nearby_locations = []
    for location in world.locations:
        distance = location_distance(
            current_location,
            location,
        )
        if distance > max_distance:
            continue

        attributes: dict[str, str | int | bool] = {
            "location_type": location.location_type.value,
            "capacity": location.capacity,
        }
        attributes.update(
            {
                f"{resource_type.value}_quantity": quantity
                for resource_type, quantity
                in location.inventory.items()
            }
        )
        nearby_locations.append(
            NearbyEntitySummary(
                entity_id=location.id,
                entity_type="location",
                name=location.name,
                distance=distance,
                attributes=attributes,
            )
        )

    return sorted(
        nearby_locations,
        key=lambda entity: (entity.distance, entity.entity_id),
    )


def build_nearby_agents(
    world: World,
    agent: Agent,
    *,
    max_distance: int = 5,
) -> list[NearbyEntitySummary]:
    if max_distance < 0:
        raise ValueError("Maximum distance cannot be negative.")

    locations_by_id = {
        location.id: location
        for location in world.locations
    }
    current_location = locations_by_id.get(agent.location_id)
    if current_location is None:
        raise ValueError("Agent references an unknown location.")

    nearby_agents = []
    for other_agent in world.agents:
        if other_agent.id == agent.id:
            continue

        other_location = locations_by_id.get(
            other_agent.location_id
        )
        if other_location is None:
            raise ValueError(
                "Nearby agent references an unknown location."
            )

        distance = location_distance(
            current_location,
            other_location,
        )
        if distance > max_distance:
            continue

        nearby_agents.append(
            NearbyEntitySummary(
                entity_id=other_agent.id,
                entity_type="agent",
                name=other_agent.name,
                distance=distance,
                attributes={
                    "occupation": other_agent.occupation.value,
                    "status": other_agent.status.value,
                    "hunger": other_agent.hunger,
                    "energy": other_agent.energy,
                    "health": other_agent.health,
                },
            )
        )

    return sorted(
        nearby_agents,
        key=lambda entity: (entity.distance, entity.entity_id),
    )


def build_decision_context(
    world: World,
    agent: Agent,
    *,
    available_actions: Sequence[AvailableAction],
    fallback_action_id: str,
    goals: Sequence[GoalSummary] = (),
    relationships: Sequence[RelationshipSummary] = (),
    memories: Sequence[RetrievedMemory] = (),
    max_distance: int = 5,
    max_nearby_entities: int = 20,
) -> DecisionContext:
    if not any(
        world_agent.id == agent.id
        for world_agent in world.agents
    ):
        raise ValueError("Agent does not belong to the world.")

    if max_nearby_entities <= 0:
        raise ValueError(
            "Maximum nearby entities must be positive."
        )

    nearby_entities = [
        *build_nearby_locations(
            world,
            agent,
            max_distance=max_distance,
        ),
        *build_nearby_agents(
            world,
            agent,
            max_distance=max_distance,
        ),
    ]
    nearby_entities.sort(
        key=lambda entity: (
            entity.distance,
            entity.entity_type,
            entity.entity_id,
        )
    )

    return DecisionContext(
        world_id=world.id,
        tick=world.current_tick,
        agent=build_agent_decision_state(agent),
        goals=list(goals),
        nearby_entities=nearby_entities[
            :max_nearby_entities
        ],
        relationships=list(relationships),
        memories=list(memories)[:5],
        available_actions=list(available_actions),
        fallback_action_id=fallback_action_id,
    )
