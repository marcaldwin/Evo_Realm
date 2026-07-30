from collections.abc import Callable
from random import Random

from ..core.enums import (
    AgentStatus,
    LocationType,
    Occupation,
    ResourceType,
)
from .engine import advance_tick, perform_farm_work, purchase_food
from .models import Agent, Location, World


DEFAULT_SIMULATION_TICKS = 100
DEMO_MARKET_PURCHASE_QUANTITY = 3
DEMO_MARKET_REORDER_LEVEL = 1

TickCallback = Callable[[World], None]


def create_demo_world(seed: int) -> World:
    randomizer = Random(seed)

    farm = Location(
        id="north-farm",
        name="North Farm",
        location_type=LocationType.FARM,
        x=1,
        y=1,
        capacity=10,
    )
    market = Location(
        id="central-market",
        name="Central Market",
        location_type=LocationType.MARKET,
        x=4,
        y=3,
        capacity=20,
        inventory={ResourceType.FOOD: 100},
    )
    clinic = Location(
        id="community-clinic",
        name="Community Clinic",
        location_type=LocationType.CLINIC,
        x=7,
        y=3,
        capacity=8,
        inventory={ResourceType.MEDICINE: 20},
    )
    town_hall = Location(
        id="town-hall",
        name="Town Hall",
        location_type=LocationType.TOWN_HALL,
        x=4,
        y=5,
        capacity=12,
    )
    hilltop_home = Location(
        id="hilltop-home",
        name="Hilltop Home",
        location_type=LocationType.HOME,
        x=1,
        y=5,
        capacity=4,
    )
    riverside_home = Location(
        id="riverside-home",
        name="Riverside Home",
        location_type=LocationType.HOME,
        x=2,
        y=7,
        capacity=4,
    )
    workshop = Location(
        id="east-workshop",
        name="East Workshop",
        location_type=LocationType.WORKSHOP,
        x=7,
        y=7,
        capacity=8,
        inventory={ResourceType.WOOD: 30},
    )

    agent_specs = [
        (
            "elena",
            "Elena",
            Occupation.FARMER,
            farm.id,
            2,
            randomizer.randint(0, 10),
        ),
        (
            "marco",
            "Marco",
            Occupation.FARMER,
            farm.id,
            2,
            randomizer.randint(0, 10),
        ),
        (
            "sofia",
            "Sofia",
            Occupation.WORKER,
            market.id,
            0,
            randomizer.randint(40, 60),
        ),
        (
            "liam",
            "Liam",
            Occupation.MERCHANT,
            market.id,
            1,
            randomizer.randint(40, 60),
        ),
        (
            "mia",
            "Mia",
            Occupation.DOCTOR,
            clinic.id,
            1,
            randomizer.randint(5, 15),
        ),
    ]

    agents = [
        Agent(
            id=agent_id,
            name=name,
            occupation=occupation,
            location_id=location_id,
            status=AgentStatus.IDLE,
            hunger=randomizer.randint(20, 60),
            energy=randomizer.randint(70, 100),
            health=randomizer.randint(85, 100),
            money=money,
            inventory={ResourceType.FOOD: food},
        )
        for agent_id, name, occupation, location_id, food, money in agent_specs
    ]

    return World(
        id=f"demo-world-{seed}",
        name="EvoRealm Demo World",
        current_tick=0,
        seed=seed,
        locations=[
            farm,
            market,
            clinic,
            town_hall,
            hilltop_home,
            riverside_home,
            workshop,
        ],
        agents=agents,
    )


def validate_world_state(world: World) -> None:
    if (
        not isinstance(world.current_tick, int)
        or isinstance(world.current_tick, bool)
        or world.current_tick < 0
    ):
        raise ValueError("World tick cannot be negative.")

    location_ids = {location.id for location in world.locations}
    if len(location_ids) != len(world.locations):
        raise ValueError("World contains duplicate location IDs.")

    occupancy = {location_id: 0 for location_id in location_ids}
    location_coordinates: set[tuple[int, int]] = set()
    for location in world.locations:
        if (
            not isinstance(location.x, int)
            or isinstance(location.x, bool)
            or not 0 <= location.x <= 9
            or not isinstance(location.y, int)
            or isinstance(location.y, bool)
            or not 0 <= location.y <= 9
        ):
            raise ValueError(
                f"Location {location.id} has invalid coordinates."
            )
        coordinate = (location.x, location.y)
        if coordinate in location_coordinates:
            raise ValueError(
                "World contains duplicate location coordinates."
            )
        location_coordinates.add(coordinate)
        if (
            not isinstance(location.capacity, int)
            or isinstance(location.capacity, bool)
            or location.capacity < 0
        ):
            raise ValueError(
                f"Location {location.id} has invalid capacity."
            )
        _validate_inventory(
            location.inventory,
            owner=f"Location {location.id}",
        )

    for agent in world.agents:
        if agent.location_id not in location_ids:
            raise ValueError(
                f"Agent {agent.id} references an unknown location."
            )
        occupancy[agent.location_id] += 1
        _validate_bounded_stat(
            agent.hunger,
            owner=f"Agent {agent.id}",
            stat_name="hunger",
        )
        _validate_bounded_stat(
            agent.energy,
            owner=f"Agent {agent.id}",
            stat_name="energy",
        )
        _validate_bounded_stat(
            agent.health,
            owner=f"Agent {agent.id}",
            stat_name="health",
        )
        if (
            not isinstance(agent.money, int)
            or isinstance(agent.money, bool)
            or agent.money < 0
        ):
            raise ValueError(f"Agent {agent.id} has invalid money.")
        _validate_inventory(agent.inventory, owner=f"Agent {agent.id}")

    for location in world.locations:
        if occupancy[location.id] > location.capacity:
            raise ValueError(
                f"Location {location.id} capacity was exceeded."
            )


def _validate_bounded_stat(
    value: int,
    *,
    owner: str,
    stat_name: str,
) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 100
    ):
        raise ValueError(f"{owner} has invalid {stat_name}.")


def _validate_inventory(
    inventory: dict[ResourceType, int],
    *,
    owner: str,
) -> None:
    for resource_type, quantity in inventory.items():
        if not isinstance(resource_type, ResourceType):
            raise ValueError(f"{owner} has an invalid resource type.")
        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity < 0
        ):
            raise ValueError(
                f"{owner} has an invalid {resource_type.value} quantity."
            )


def _perform_demo_actions(world: World) -> None:
    locations_by_id = {
        location.id: location
        for location in world.locations
    }

    for agent in world.agents:
        if agent.occupation == Occupation.FARMER:
            perform_farm_work(agent, world)

        location = locations_by_id[agent.location_id]
        food_quantity = agent.inventory.get(ResourceType.FOOD, 0)
        if (
            location.location_type == LocationType.MARKET
            and food_quantity <= DEMO_MARKET_REORDER_LEVEL
        ):
            purchase_food(
                agent,
                world,
                quantity=DEMO_MARKET_PURCHASE_QUANTITY,
            )


def run_demo_simulation(
    seed: int,
    ticks: int = DEFAULT_SIMULATION_TICKS,
    on_tick: TickCallback | None = None,
) -> World:
    world = create_demo_world(seed)
    return run_simulation(world, ticks=ticks, on_tick=on_tick)


def run_simulation(
    world: World,
    ticks: int = DEFAULT_SIMULATION_TICKS,
    on_tick: TickCallback | None = None,
) -> World:
    if not isinstance(ticks, int) or isinstance(ticks, bool) or ticks < 0:
        raise ValueError("Ticks must be a non-negative integer.")

    validate_world_state(world)

    for _ in range(ticks):
        advance_tick(world)
        _perform_demo_actions(world)
        validate_world_state(world)
        if on_tick is not None:
            on_tick(world)

    return world
