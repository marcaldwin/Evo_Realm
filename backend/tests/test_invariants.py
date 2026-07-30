import pytest

from backend.app.core.enums import ResourceType
from backend.app.simulation.engine import purchase_food
from backend.app.simulation.runner import (
    create_demo_world,
    run_demo_simulation,
    validate_world_state,
)


@pytest.mark.parametrize("seed", [0, 1, 42, 9999])
def test_one_hundred_tick_runs_preserve_all_world_invariants(
    seed: int,
) -> None:
    world = run_demo_simulation(seed=seed, ticks=100)

    validate_world_state(world)

    assert world.current_tick == 100
    assert len(world.agents) == 5


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("hunger", -1),
        ("hunger", 101),
        ("energy", -1),
        ("energy", 101),
        ("health", -1),
        ("health", 101),
    ],
)
def test_validator_rejects_out_of_bounds_agent_stats(
    attribute: str,
    value: int,
) -> None:
    world = create_demo_world(seed=42)
    setattr(world.agents[0], attribute, value)

    with pytest.raises(ValueError, match=attribute):
        validate_world_state(world)


def test_validator_rejects_negative_agent_money() -> None:
    world = create_demo_world(seed=42)
    world.agents[0].money = -1

    with pytest.raises(ValueError, match="money"):
        validate_world_state(world)


def test_validator_rejects_negative_agent_inventory() -> None:
    world = create_demo_world(seed=42)
    world.agents[0].inventory[ResourceType.FOOD] = -1

    with pytest.raises(ValueError, match="food quantity"):
        validate_world_state(world)


def test_validator_rejects_negative_location_inventory() -> None:
    world = create_demo_world(seed=42)
    world.locations[1].inventory[ResourceType.FOOD] = -1

    with pytest.raises(ValueError, match="food quantity"):
        validate_world_state(world)


def test_validator_rejects_unknown_agent_location() -> None:
    world = create_demo_world(seed=42)
    world.agents[0].location_id = "missing-location"

    with pytest.raises(ValueError, match="unknown location"):
        validate_world_state(world)


def test_validator_rejects_exceeded_location_capacity() -> None:
    world = create_demo_world(seed=42)
    farm = next(
        location
        for location in world.locations
        if location.id == "north-farm"
    )
    farm.capacity = 1

    with pytest.raises(ValueError, match="capacity was exceeded"):
        validate_world_state(world)


def test_validator_rejects_invalid_location_capacity() -> None:
    world = create_demo_world(seed=42)
    world.locations[0].capacity = -1

    with pytest.raises(ValueError, match="invalid capacity"):
        validate_world_state(world)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("x", -1),
        ("x", 10),
        ("y", -1),
        ("y", 10),
    ],
)
def test_validator_rejects_out_of_bounds_location_coordinates(
    axis: str,
    value: int,
) -> None:
    world = create_demo_world(seed=42)
    setattr(world.locations[0], axis, value)

    with pytest.raises(ValueError, match="invalid coordinates"):
        validate_world_state(world)


def test_validator_rejects_duplicate_location_coordinates() -> None:
    world = create_demo_world(seed=42)
    world.locations[1].x = world.locations[0].x
    world.locations[1].y = world.locations[0].y

    with pytest.raises(ValueError, match="duplicate location coordinates"):
        validate_world_state(world)


def test_successful_purchase_conserves_transferred_food() -> None:
    world = create_demo_world(seed=42)
    buyer = next(agent for agent in world.agents if agent.id == "sofia")
    market = next(
        location
        for location in world.locations
        if location.id == "central-market"
    )
    food_before = (
        buyer.inventory[ResourceType.FOOD]
        + market.inventory[ResourceType.FOOD]
    )

    purchased = purchase_food(buyer, world, quantity=3)

    food_after = (
        buyer.inventory[ResourceType.FOOD]
        + market.inventory[ResourceType.FOOD]
    )
    assert purchased is True
    assert food_after == food_before


def test_rejected_purchase_preserves_all_transfer_state() -> None:
    world = create_demo_world(seed=42)
    buyer = next(agent for agent in world.agents if agent.id == "sofia")
    market = next(
        location
        for location in world.locations
        if location.id == "central-market"
    )
    buyer.money = 0
    state_before = (
        buyer.money,
        buyer.inventory[ResourceType.FOOD],
        market.inventory[ResourceType.FOOD],
    )

    purchased = purchase_food(buyer, world, quantity=3)

    state_after = (
        buyer.money,
        buyer.inventory[ResourceType.FOOD],
        market.inventory[ResourceType.FOOD],
    )
    assert purchased is False
    assert state_after == state_before


def test_same_seed_reproduces_identical_one_hundred_tick_result() -> None:
    first_world = run_demo_simulation(seed=2026, ticks=100)
    second_world = run_demo_simulation(seed=2026, ticks=100)

    assert first_world == second_world
