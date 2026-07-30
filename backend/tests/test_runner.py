import pytest

from backend.app.core.enums import (
    EventType,
    LocationType,
    ResourceType,
)
from backend.app.simulation.runner import (
    create_demo_world,
    run_demo_simulation,
    validate_world_state,
)


def test_same_seed_creates_the_same_initial_world() -> None:
    first_world = create_demo_world(seed=42)
    second_world = create_demo_world(seed=42)

    assert first_world == second_world


def test_different_seeds_create_different_initial_worlds() -> None:
    first_world = create_demo_world(seed=42)
    second_world = create_demo_world(seed=43)

    assert first_world != second_world


def test_demo_world_contains_five_agents_and_initialized_state() -> None:
    world = create_demo_world(seed=42)

    assert len(world.agents) == 5
    assert len(world.locations) == 7
    assert {
        location.location_type
        for location in world.locations
    } == set(LocationType)
    assert len({
        (location.x, location.y)
        for location in world.locations
    }) == len(world.locations)
    assert all(
        0 <= location.x <= 9 and 0 <= location.y <= 9
        for location in world.locations
    )
    assert world.current_tick == 0
    assert world.events == []
    assert all(agent.inventory for agent in world.agents)


def test_demo_simulation_completes_one_hundred_ticks() -> None:
    world = run_demo_simulation(seed=42)

    assert world.current_tick == 100
    assert len(world.agents) == 5
    assert world.events


def test_demo_simulation_keeps_all_state_valid() -> None:
    world = run_demo_simulation(seed=42)

    validate_world_state(world)

    for agent in world.agents:
        assert 0 <= agent.hunger <= 100
        assert 0 <= agent.energy <= 100
        assert 0 <= agent.health <= 100
        assert agent.money >= 0
        assert all(quantity >= 0 for quantity in agent.inventory.values())

    for location in world.locations:
        assert all(
            quantity >= 0
            for quantity in location.inventory.values()
        )


def test_demo_simulation_exercises_first_sprint_rules() -> None:
    world = run_demo_simulation(seed=42)
    event_types = {event.event_type for event in world.events}

    assert {
        EventType.FARM_WORK_SUCCEEDED,
        EventType.FARM_WORK_REJECTED,
        EventType.WAGE_EARNED,
        EventType.FOOD_PURCHASED,
        EventType.FOOD_CONSUMED,
        EventType.FOOD_CONSUMPTION_REJECTED,
        EventType.RESTED,
    } <= event_types


def test_demo_simulation_final_state_and_events_are_inspectable() -> None:
    world = run_demo_simulation(seed=42)

    assert all(1 <= event.tick <= 100 for event in world.events)
    assert all(event.summary.startswith("Tick ") for event in world.events)

    market = next(
        location
        for location in world.locations
        if location.id == "central-market"
    )
    assert market.inventory[ResourceType.FOOD] < 100

    farmers = [
        agent
        for agent in world.agents
        if agent.id in {"elena", "marco"}
    ]
    assert all(agent.money > 0 for agent in farmers)
    assert all(agent.inventory[ResourceType.FOOD] > 2 for agent in farmers)


@pytest.mark.parametrize("ticks", [-1, 1.5, True])
def test_demo_simulation_rejects_invalid_tick_counts(ticks: object) -> None:
    with pytest.raises(ValueError, match="Ticks"):
        run_demo_simulation(seed=42, ticks=ticks)  # type: ignore[arg-type]
