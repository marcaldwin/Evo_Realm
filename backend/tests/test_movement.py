from copy import deepcopy

from backend.app.core.enums import (
    AgentStatus,
    EventType,
    LocationType,
    Occupation,
    WorldStatus,
)
from backend.app.simulation.engine import (
    advance_tick,
    apply_automatic_movement,
    move_agent,
)
from backend.app.simulation.models import Agent, Location, World


def build_world() -> World:
    return World(
        id="movement-world",
        name="Movement World",
        current_tick=0,
        seed=42,
        status=WorldStatus.RUNNING,
        locations=[
            Location(
                id="home",
                name="Home",
                location_type=LocationType.HOME,
                x=0,
                y=0,
                capacity=2,
            ),
            Location(
                id="market",
                name="Market",
                location_type=LocationType.MARKET,
                x=1,
                y=0,
                capacity=2,
            ),
            Location(
                id="farm",
                name="Farm",
                location_type=LocationType.FARM,
                x=2,
                y=0,
                capacity=2,
            ),
        ],
        agents=[
            Agent(
                id="elena",
                name="Elena",
                occupation=Occupation.FARMER,
                location_id="home",
                status=AgentStatus.IDLE,
                hunger=20,
                energy=90,
                health=100,
                money=5,
            )
        ],
    )


def test_valid_movement_updates_location_and_records_event() -> None:
    world = build_world()
    agent = world.agents[0]

    moved = move_agent(agent, world, "market")

    assert moved is True
    assert agent.location_id == "market"
    assert world.events[-1].event_type == EventType.AGENT_MOVED
    assert world.events[-1].location_id == "market"
    assert world.events[-1].summary == (
        "Tick 0: Elena moved from Home to Market."
    )


def test_movement_rejects_full_destination_without_partial_change() -> None:
    world = build_world()
    world.locations[1].capacity = 1
    world.agents.append(
        Agent(
            id="liam",
            name="Liam",
            occupation=Occupation.MERCHANT,
            location_id="market",
            status=AgentStatus.IDLE,
            hunger=20,
            energy=90,
            health=100,
            money=5,
        )
    )
    agent = world.agents[0]

    moved = move_agent(agent, world, "market")

    assert moved is False
    assert agent.location_id == "home"
    assert world.events[-1].event_type == (
        EventType.AGENT_MOVEMENT_REJECTED
    )
    assert "at capacity" in world.events[-1].summary


def test_movement_rejects_invalid_or_unavailable_agents() -> None:
    world = build_world()
    agent = world.agents[0]

    assert move_agent(agent, world, "missing") is False
    assert agent.location_id == "home"

    agent.status = AgentStatus.RESTING

    assert move_agent(agent, world, "market") is False
    assert agent.location_id == "home"


def test_automatic_movement_uses_next_available_location() -> None:
    world = build_world()
    world.locations[1].capacity = 0

    apply_automatic_movement(world)

    assert world.agents[0].location_id == "farm"


def test_running_tick_moves_agents_but_created_tick_does_not() -> None:
    running_world = build_world()
    created_world = deepcopy(running_world)
    created_world.status = WorldStatus.CREATED

    advance_tick(running_world)
    advance_tick(created_world)

    assert running_world.agents[0].location_id == "market"
    assert created_world.agents[0].location_id == "home"


def test_automatic_movement_is_deterministic() -> None:
    first_world = build_world()
    second_world = deepcopy(first_world)

    for _ in range(5):
        advance_tick(first_world)
        advance_tick(second_world)

    assert first_world == second_world
