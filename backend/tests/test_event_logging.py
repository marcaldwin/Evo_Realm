from backend.app.core.enums import (
    AgentStatus,
    EventType,
    LocationType,
    Occupation,
    ResourceType,
)
from backend.app.simulation.engine import (
    advance_tick,
    perform_farm_work,
    purchase_food,
)
from backend.app.simulation.models import Agent, Location, World


def make_world(
    *,
    tick: int,
    agent_name: str,
    location_name: str,
    location_type: LocationType,
    hunger: int = 10,
    energy: int = 100,
    money: int = 0,
    agent_food: int = 0,
    location_food: int = 0,
    occupation: Occupation = Occupation.FARMER,
) -> tuple[Agent, Location, World]:
    location = Location(
        id="test-location",
        name=location_name,
        location_type=location_type,
        x=0,
        y=0,
        capacity=10,
        inventory={ResourceType.FOOD: location_food},
    )
    agent = Agent(
        id="test-agent",
        name=agent_name,
        occupation=occupation,
        location_id=location.id,
        status=AgentStatus.IDLE,
        hunger=hunger,
        energy=energy,
        health=100,
        money=money,
        inventory={ResourceType.FOOD: agent_food},
    )
    world = World(
        id="test-world",
        name="Test World",
        current_tick=tick,
        seed=1,
        locations=[location],
        agents=[agent],
    )
    return agent, location, world


def test_successful_farm_work_records_production_and_wage_events() -> None:
    agent, farm, world = make_world(
        tick=12,
        agent_name="Elena",
        location_name="North Farm",
        location_type=LocationType.FARM,
    )

    perform_farm_work(agent, world)

    assert [event.event_type for event in world.events] == [
        EventType.FARM_WORK_SUCCEEDED,
        EventType.WAGE_EARNED,
    ]
    assert all(event.tick == 12 for event in world.events)
    assert all(event.agent_id == agent.id for event in world.events)
    assert all(event.location_id == farm.id for event in world.events)
    assert world.events[0].summary == (
        "Tick 12: Elena produced 5 food at North Farm."
    )
    assert world.events[1].summary == (
        "Tick 12: Elena earned 10 money from farm work."
    )


def test_rejected_farm_work_records_the_failure_reason() -> None:
    agent, home, world = make_world(
        tick=14,
        agent_name="Marco",
        location_name="Marco's Home",
        location_type=LocationType.HOME,
    )

    perform_farm_work(agent, world)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.event_type == EventType.FARM_WORK_REJECTED
    assert event.agent_id == agent.id
    assert event.location_id == home.id
    assert event.summary == (
        "Tick 14: Marco failed to work at the farm because "
        "they are not located at a farm."
    )


def test_successful_purchase_records_market_and_price() -> None:
    agent, market, world = make_world(
        tick=18,
        agent_name="Sofia",
        location_name="Central Market",
        location_type=LocationType.MARKET,
        money=10,
        location_food=5,
        occupation=Occupation.WORKER,
    )

    purchase_food(agent, world, quantity=1)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.event_type == EventType.FOOD_PURCHASED
    assert event.agent_id == agent.id
    assert event.location_id == market.id
    assert event.summary == (
        "Tick 18: Sofia purchased 1 food from Central Market for 2 money."
    )


def test_rejected_purchase_records_the_failure_reason() -> None:
    agent, market, world = make_world(
        tick=20,
        agent_name="Liam",
        location_name="Central Market",
        location_type=LocationType.MARKET,
        money=1,
        location_food=5,
        occupation=Occupation.WORKER,
    )

    purchase_food(agent, world, quantity=1)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.event_type == EventType.FOOD_PURCHASE_REJECTED
    assert event.agent_id == agent.id
    assert event.location_id == market.id
    assert event.summary == (
        "Tick 20: Liam failed to purchase food because they lacked money."
    )


def test_automatic_eating_records_consumed_food() -> None:
    agent, location, world = make_world(
        tick=7,
        agent_name="Ava",
        location_name="Ava's Home",
        location_type=LocationType.HOME,
        hunger=68,
        agent_food=1,
    )

    advance_tick(world)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.event_type == EventType.FOOD_CONSUMED
    assert event.tick == 8
    assert event.agent_id == agent.id
    assert event.location_id == location.id
    assert event.summary == (
        "Tick 8: Ava consumed 1 food and reduced hunger by 30."
    )


def test_failed_automatic_eating_records_missing_food() -> None:
    _, _, world = make_world(
        tick=8,
        agent_name="Noah",
        location_name="Noah's Home",
        location_type=LocationType.HOME,
        hunger=68,
        agent_food=0,
    )

    advance_tick(world)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.event_type == EventType.FOOD_CONSUMPTION_REJECTED
    assert event.summary == (
        "Tick 9: Noah failed to eat because they had no food."
    )


def test_automatic_resting_records_recovered_energy() -> None:
    agent, location, world = make_world(
        tick=10,
        agent_name="Mia",
        location_name="Mia's Home",
        location_type=LocationType.HOME,
        energy=21,
    )

    advance_tick(world)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.event_type == EventType.RESTED
    assert event.tick == 11
    assert event.agent_id == agent.id
    assert event.location_id == location.id
    assert event.summary == (
        "Tick 11: Mia rested and recovered 30 energy."
    )
