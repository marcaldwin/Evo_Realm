from backend.app.core.enums import AgentStatus, Occupation, ResourceType
from backend.app.simulation.engine import advance_tick
from backend.app.simulation.models import Agent, World


def test_agent_inventory_defaults_to_an_independent_empty_dictionary() -> None:
    first_agent = Agent(
        id="first-agent",
        name="First Agent",
        occupation=Occupation.FARMER,
        location_id="test-location",
        status=AgentStatus.IDLE,
        hunger=10,
        energy=100,
        health=100,
        money=0,
    )
    second_agent = Agent(
        id="second-agent",
        name="Second Agent",
        occupation=Occupation.WORKER,
        location_id="test-location",
        status=AgentStatus.IDLE,
        hunger=10,
        energy=100,
        health=100,
        money=0,
    )

    first_agent.inventory[ResourceType.FOOD] = 2

    assert first_agent.inventory == {ResourceType.FOOD: 2}
    assert second_agent.inventory == {}


def test_agent_inventory_accepts_resource_quantities() -> None:
    inventory = {
        ResourceType.FOOD: 3,
        ResourceType.MEDICINE: 1,
        ResourceType.WOOD: 5,
    }

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
        inventory=inventory,
    )

    assert agent.inventory == inventory


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


def test_advance_tick_decreases_agent_energy_by_one() -> None:
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        occupation=Occupation.FARMER,
        location_id="test-location",
        status=AgentStatus.IDLE,
        hunger=10,
        energy=50,
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

    assert agent.energy == 49


def test_advance_tick_clamps_agent_energy_at_zero() -> None:
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        occupation=Occupation.FARMER,
        location_id="test-location",
        status=AgentStatus.IDLE,
        hunger=10,
        energy=0,
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

    assert agent.energy == 0
