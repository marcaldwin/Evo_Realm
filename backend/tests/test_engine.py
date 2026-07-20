from backend.app.core.enums import AgentStatus, Occupation
from backend.app.simulation.engine import advance_tick
from backend.app.simulation.models import Agent, World


def test_advance_tick_increases_current_tick() -> None:
    world = World(
        id="test-world",
        name="Test World",
        current_tick=0,
        seed=1,
        locations=[],
        agents=[],
    )

    advance_tick(world)

    assert world.current_tick == 1


def test_advance_tick_increases_agent_hunger_by_two() -> None:
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        occupation=Occupation.FARMER,
        location_id="test-location",
        status=AgentStatus.IDLE,
        hunger=10,
        energy=100,
        health=100,
        money=0,
    )
    world = World(
        id="test-world",
        name="Test World",
        current_tick=0,
        seed=1,
        locations=[],
        agents=[agent],
    )

    advance_tick(world)

    assert agent.hunger == 12


def test_advance_tick_clamps_agent_hunger_at_one_hundred() -> None:
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        occupation=Occupation.FARMER,
        location_id="test-location",
        status=AgentStatus.IDLE,
        hunger=99,
        energy=100,
        health=100,
        money=0,
    )
    world = World(
        id="test-world",
        name="Test World",
        current_tick=0,
        seed=1,
        locations=[],
        agents=[agent],
    )

    advance_tick(world)

    assert agent.hunger == 100
