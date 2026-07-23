from backend.app.core.enums import EventType, LocationType, ResourceType
from backend.app.simulation.models import Location, SimulationEvent, World


def test_location_inventory_defaults_to_an_independent_empty_dictionary() -> None:
    first_location = Location(
        id="first-location",
        name="First Location",
        location_type=LocationType.MARKET,
        x=0,
        y=0,
        capacity=10,
    )
    second_location = Location(
        id="second-location",
        name="Second Location",
        location_type=LocationType.MARKET,
        x=1,
        y=1,
        capacity=10,
    )

    first_location.inventory[ResourceType.FOOD] = 5

    assert first_location.inventory == {ResourceType.FOOD: 5}
    assert second_location.inventory == {}


def test_location_inventory_accepts_resource_quantities() -> None:
    inventory = {
        ResourceType.FOOD: 10,
        ResourceType.MEDICINE: 2,
        ResourceType.WOOD: 4,
    }

    location = Location(
        id="test-market",
        name="Test Market",
        location_type=LocationType.MARKET,
        x=0,
        y=0,
        capacity=10,
        inventory=inventory,
    )

    assert location.inventory == inventory


def test_world_events_default_to_an_independent_empty_list() -> None:
    first_world = World(
        id="first-world",
        name="First World",
        current_tick=0,
        seed=1,
        locations=[],
        agents=[],
    )
    second_world = World(
        id="second-world",
        name="Second World",
        current_tick=0,
        seed=2,
        locations=[],
        agents=[],
    )

    event = SimulationEvent(
        tick=1,
        event_type=EventType.RESTED,
        agent_id="test-agent",
        location_id="test-location",
        summary="Tick 1: Test Agent rested.",
    )
    first_world.events.append(event)

    assert first_world.events == [event]
    assert second_world.events == []
