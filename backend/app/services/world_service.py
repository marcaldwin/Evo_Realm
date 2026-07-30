from dataclasses import dataclass
from uuid import uuid4
from copy import deepcopy

from ..api.schemas.world import WorldCreate
from ..core.enums import WorldStatus
from ..db.session import SessionLocal
from ..memory.repository import MemoryRepository
from ..memory.schemas import RetrievedMemory
from ..repositories.world_repository import WorldRepository
from ..simulation.engine import advance_tick
from ..simulation.models import (
    Agent,
    Location,
    SimulationEvent,
    World,
)


@dataclass(frozen=True)
class WorldSummary:
    id: str
    name: str
    current_tick: int
    seed: int
    status: WorldStatus
    agent_count: int


@dataclass(frozen=True)
class WorldStepResult:
    previous_world: World
    updated_world: World


@dataclass(frozen=True)
class AgentInspectorData:
    agent: Agent
    recent_actions: list[SimulationEvent]
    selected_retrieved_memories: list[RetrievedMemory]


class InvalidWorldTransitionError(Exception):
    def __init__(
        self,
        action: str,
        current_status: WorldStatus,
    ) -> None:
        self.action = action
        self.current_status = current_status
        super().__init__(
            f"Cannot {action} world while status is "
            f"{current_status.value}."
        )


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
            personality_traits=dict(agent.personality_traits),
            active_goal=agent.active_goal,
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
    with SessionLocal.begin() as session:
        WorldRepository(session).add(world)
    return world


def get_world(world_id: str) -> World | None:
    with SessionLocal() as session:
        return WorldRepository(session).get(world_id)


def list_worlds() -> list[WorldSummary]:
    with SessionLocal() as session:
        summaries = WorldRepository(session).list_summaries()
        return [
            WorldSummary(
                id=summary.id,
                name=summary.name,
                current_tick=summary.current_tick,
                seed=summary.seed,
                status=summary.status,
                agent_count=summary.agent_count,
            )
            for summary in summaries
        ]


def list_running_world_ids() -> list[str]:
    return [
        summary.id
        for summary in list_worlds()
        if summary.status == WorldStatus.RUNNING
    ]


def list_world_agents(world_id: str) -> list[Agent] | None:
    world = get_world(world_id)
    if world is None:
        return None
    return list(world.agents)


def get_world_agent(
    world_id: str,
    agent_id: str,
) -> Agent | None:
    world = get_world(world_id)
    if world is None:
        return None

    return next(
        (
            agent
            for agent in world.agents
            if agent.id == agent_id
        ),
        None,
    )


def get_world_agent_inspector(
    world_id: str,
    agent_id: str,
) -> AgentInspectorData | None:
    with SessionLocal() as session:
        world = WorldRepository(session).get(world_id)
        if world is None:
            return None

        agent = next(
            (
                candidate
                for candidate in world.agents
                if candidate.id == agent_id
            ),
            None,
        )
        if agent is None:
            return None

        recent_actions = list(
            reversed(
                [
                    event
                    for event in world.events
                    if event.agent_id == agent_id
                ]
            )
        )[:5]
        selected_retrieved_memories = (
            MemoryRepository(session).list_latest_retrieved_memories(
                world_id=world_id,
                owner_agent_id=agent_id,
            )
        )
        return AgentInspectorData(
            agent=agent,
            recent_actions=recent_actions,
            selected_retrieved_memories=selected_retrieved_memories,
        )


def list_world_events(world_id: str) -> list[SimulationEvent] | None:
    world = get_world(world_id)
    if world is None:
        return None
    return list(world.events)


def step_world_with_result(
    world_id: str,
) -> WorldStepResult | None:
    with SessionLocal.begin() as session:
        repository = WorldRepository(session)
        world = repository.get(world_id, for_update=True)
        if world is None:
            return None

        previous_world = deepcopy(world)
        updated_world = advance_tick(world)
        repository.save(updated_world)
        result = WorldStepResult(
            previous_world=previous_world,
            updated_world=updated_world,
        )

    return result


def step_world(world_id: str) -> World | None:
    result = step_world_with_result(world_id)
    if result is None:
        return None
    return result.updated_world


def step_running_world_with_result(
    world_id: str,
) -> WorldStepResult | None:
    with SessionLocal.begin() as session:
        repository = WorldRepository(session)
        world = repository.get(world_id, for_update=True)
        if world is None or world.status != WorldStatus.RUNNING:
            return None

        previous_world = deepcopy(world)
        updated_world = advance_tick(world)
        repository.save(updated_world)
        result = WorldStepResult(
            previous_world=previous_world,
            updated_world=updated_world,
        )

    return result


def _transition_world(
    world_id: str,
    *,
    action: str,
    required_status: WorldStatus,
    target_status: WorldStatus,
) -> World | None:
    with SessionLocal.begin() as session:
        repository = WorldRepository(session)
        world = repository.get(world_id, for_update=True)
        if world is None:
            return None

        if world.status != required_status:
            raise InvalidWorldTransitionError(
                action,
                world.status,
            )

        world.status = target_status
        repository.save(world)
        return world


def start_world(world_id: str) -> World | None:
    return _transition_world(
        world_id,
        action="start",
        required_status=WorldStatus.CREATED,
        target_status=WorldStatus.RUNNING,
    )


def pause_world(world_id: str) -> World | None:
    return _transition_world(
        world_id,
        action="pause",
        required_status=WorldStatus.RUNNING,
        target_status=WorldStatus.PAUSED,
    )


def resume_world(world_id: str) -> World | None:
    return _transition_world(
        world_id,
        action="resume",
        required_status=WorldStatus.PAUSED,
        target_status=WorldStatus.RUNNING,
    )
