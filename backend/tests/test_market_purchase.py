import pytest

from backend.app.core.enums import (
    AgentStatus,
    LocationType,
    Occupation,
    ResourceType,
)
from backend.app.simulation.engine import purchase_food
from backend.app.simulation.models import Agent, Location, World


def make_market_world(
    *,
    money: int = 20,
    buyer_food: int = 0,
    market_food: int = 10,
    location_type: LocationType = LocationType.MARKET,
) -> tuple[Agent, Location, World]:
    market = Location(
        id="test-market",
        name="Test Market",
        location_type=location_type,
        x=0,
        y=0,
        capacity=10,
        inventory={ResourceType.FOOD: market_food},
    )
    buyer = Agent(
        id="test-buyer",
        name="Test Buyer",
        occupation=Occupation.WORKER,
        location_id=market.id,
        status=AgentStatus.IDLE,
        hunger=10,
        energy=100,
        health=100,
        money=money,
        inventory={ResourceType.FOOD: buyer_food},
    )
    world = World(
        id="test-world",
        name="Test World",
        current_tick=0,
        seed=1,
        locations=[market],
        agents=[buyer],
    )
    return buyer, market, world


def test_valid_market_purchase_transfers_food_and_deducts_money() -> None:
    buyer, market, world = make_market_world(
        money=20,
        buyer_food=1,
        market_food=10,
    )

    purchased = purchase_food(buyer, world, quantity=3)

    assert purchased is True
    assert buyer.money == 14
    assert buyer.inventory[ResourceType.FOOD] == 4
    assert market.inventory[ResourceType.FOOD] == 7


@pytest.mark.parametrize(
    ("money", "buyer_food", "market_food", "quantity"),
    [
        (5, 1, 10, 3),
        (20, 1, 2, 3),
        (-1, 1, 10, 1),
        (20, -1, 10, 1),
        (20, 1, -1, 1),
    ],
)
def test_invalid_market_purchase_does_not_partially_change_state(
    money: int,
    buyer_food: int,
    market_food: int,
    quantity: int,
) -> None:
    buyer, market, world = make_market_world(
        money=money,
        buyer_food=buyer_food,
        market_food=market_food,
    )

    purchased = purchase_food(buyer, world, quantity)

    assert purchased is False
    assert buyer.money == money
    assert buyer.inventory[ResourceType.FOOD] == buyer_food
    assert market.inventory[ResourceType.FOOD] == market_food


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
def test_market_purchase_rejects_invalid_quantity_without_changes(
    quantity: object,
) -> None:
    buyer, market, world = make_market_world(
        money=20,
        buyer_food=1,
        market_food=10,
    )

    purchased = purchase_food(buyer, world, quantity)  # type: ignore[arg-type]

    assert purchased is False
    assert buyer.money == 20
    assert buyer.inventory[ResourceType.FOOD] == 1
    assert market.inventory[ResourceType.FOOD] == 10


def test_market_purchase_is_rejected_outside_a_market() -> None:
    buyer, location, world = make_market_world(
        location_type=LocationType.HOME,
    )

    purchased = purchase_food(buyer, world, quantity=1)

    assert purchased is False
    assert buyer.money == 20
    assert buyer.inventory[ResourceType.FOOD] == 0
    assert location.inventory[ResourceType.FOOD] == 10


def test_market_purchase_is_rejected_when_buyer_location_is_missing() -> None:
    buyer, market, world = make_market_world()
    buyer.location_id = "missing-location"

    purchased = purchase_food(buyer, world, quantity=1)

    assert purchased is False
    assert buyer.money == 20
    assert buyer.inventory[ResourceType.FOOD] == 0
    assert market.inventory[ResourceType.FOOD] == 10


def test_market_purchase_with_exact_money_and_stock_ends_at_zero() -> None:
    buyer, market, world = make_market_world(
        money=6,
        buyer_food=0,
        market_food=3,
    )

    purchased = purchase_food(buyer, world, quantity=3)

    assert purchased is True
    assert buyer.money == 0
    assert buyer.inventory[ResourceType.FOOD] == 3
    assert market.inventory[ResourceType.FOOD] == 0
