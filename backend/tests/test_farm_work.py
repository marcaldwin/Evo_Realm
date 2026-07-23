import pytest

from backend.app.core.enums import (
    AgentStatus,
    LocationType,
    Occupation,
    ResourceType,
)
from backend.app.simulation.engine import perform_farm_work
from backend.app.simulation.models import Agent, Location, World


def make_farm_world(
    *,
    occupation: Occupation = Occupation.FARMER,
    location_type: LocationType = LocationType.FARM,
    health: int = 100,
    energy: int = 100,
    status: AgentStatus = AgentStatus.IDLE,
    food: int = 0,
    money: int = 0,
) -> tuple[Agent, World]:
    location = Location(
        id="test-location",
        name="Test Location",
        location_type=location_type,
        x=0,
        y=0,
        capacity=10,
    )
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        occupation=occupation,
        location_id=location.id,
        status=status,
        hunger=10,
        energy=energy,
        health=health,
        money=money,
        inventory={ResourceType.FOOD: food},
    )
    world = World(
        id="test-world",
        name="Test World",
        current_tick=0,
        seed=1,
        locations=[location],
        agents=[agent],
    )
    return agent, world


def test_valid_farm_work_produces_food_costs_energy_and_pays_wage() -> None:
    agent, world = make_farm_world(energy=50, food=2, money=3)

    worked = perform_farm_work(agent, world)

    assert worked is True
    assert agent.inventory[ResourceType.FOOD] == 7
    assert agent.energy == 40
    assert agent.money == 13
    assert agent.status == AgentStatus.WORKING


@pytest.mark.parametrize(
    ("occupation", "location_type", "health", "energy", "status"),
    [
        (
            Occupation.WORKER,
            LocationType.FARM,
            100,
            50,
            AgentStatus.IDLE,
        ),
        (
            Occupation.FARMER,
            LocationType.HOME,
            100,
            50,
            AgentStatus.IDLE,
        ),
        (
            Occupation.FARMER,
            LocationType.FARM,
            0,
            50,
            AgentStatus.IDLE,
        ),
        (
            Occupation.FARMER,
            LocationType.FARM,
            100,
            9,
            AgentStatus.IDLE,
        ),
        (
            Occupation.FARMER,
            LocationType.FARM,
            100,
            50,
            AgentStatus.RESTING,
        ),
        (
            Occupation.FARMER,
            LocationType.FARM,
            100,
            50,
            AgentStatus.INCAPACITATED,
        ),
    ],
)
def test_invalid_farm_work_is_rejected_without_changing_agent(
    occupation: Occupation,
    location_type: LocationType,
    health: int,
    energy: int,
    status: AgentStatus,
) -> None:
    agent, world = make_farm_world(
        occupation=occupation,
        location_type=location_type,
        health=health,
        energy=energy,
        status=status,
        food=2,
    )

    worked = perform_farm_work(agent, world)

    assert worked is False
    assert agent.inventory[ResourceType.FOOD] == 2
    assert agent.energy == energy
    assert agent.money == 0
    assert agent.status == status


def test_farm_work_is_rejected_when_location_does_not_exist() -> None:
    agent, world = make_farm_world(energy=50, food=2)
    world.locations = []

    worked = perform_farm_work(agent, world)

    assert worked is False
    assert agent.inventory[ResourceType.FOOD] == 2
    assert agent.energy == 50
    assert agent.money == 0
    assert agent.status == AgentStatus.IDLE


def test_farm_work_with_exact_energy_cost_never_makes_energy_negative() -> None:
    agent, world = make_farm_world(energy=10)

    worked = perform_farm_work(agent, world)

    assert worked is True
    assert agent.energy == 0
    assert agent.inventory[ResourceType.FOOD] == 5
    assert agent.money == 10


def test_farm_work_repairs_negative_food_before_producing() -> None:
    agent, world = make_farm_world(food=-3)

    worked = perform_farm_work(agent, world)

    assert worked is True
    assert agent.inventory[ResourceType.FOOD] == 5


def test_farm_work_repairs_negative_money_before_paying_wage() -> None:
    agent, world = make_farm_world(money=-3)

    worked = perform_farm_work(agent, world)

    assert worked is True
    assert agent.money == 10
