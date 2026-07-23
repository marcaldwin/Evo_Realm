from ..core.enums import (
    AgentStatus,
    EventType,
    LocationType,
    Occupation,
    ResourceType,
)
from .models import Agent, SimulationEvent, World


EATING_HUNGER_THRESHOLD = 70
FOOD_HUNGER_REDUCTION = 30
RESTING_ENERGY_THRESHOLD = 20
RESTING_ENERGY_RECOVERY = 30
FARM_WORK_ENERGY_COST = 10
FARM_WORK_FOOD_YIELD = 5
FARM_WORK_WAGE = 10
MARKET_FOOD_UNIT_PRICE = 2

FARM_WORK_ALLOWED_STATUSES = frozenset(
    {
        AgentStatus.IDLE,
        AgentStatus.WORKING,
    }
)


def record_event(
    world: World,
    event_type: EventType,
    agent: Agent,
    summary: str,
) -> None:
    world.events.append(
        SimulationEvent(
            tick=world.current_tick,
            event_type=event_type,
            agent_id=agent.id,
            location_id=agent.location_id,
            summary=summary,
        )
    )


def apply_automatic_eating(agent: Agent, world: World) -> None:
    food_quantity = agent.inventory.get(ResourceType.FOOD, 0)

    if agent.hunger < EATING_HUNGER_THRESHOLD:
        return

    if food_quantity <= 0:
        record_event(
            world,
            EventType.FOOD_CONSUMPTION_REJECTED,
            agent,
            (
                f"Tick {world.current_tick}: {agent.name} failed to eat "
                "because they had no food."
            ),
        )
        return

    hunger_before_eating = agent.hunger
    agent.inventory[ResourceType.FOOD] = food_quantity - 1
    agent.hunger = max(agent.hunger - FOOD_HUNGER_REDUCTION, 0)
    hunger_reduced = hunger_before_eating - agent.hunger
    record_event(
        world,
        EventType.FOOD_CONSUMED,
        agent,
        (
            f"Tick {world.current_tick}: {agent.name} consumed 1 food "
            f"and reduced hunger by {hunger_reduced}."
        ),
    )


def apply_automatic_resting(agent: Agent, world: World) -> None:
    if agent.energy > RESTING_ENERGY_THRESHOLD:
        if agent.status == AgentStatus.RESTING:
            agent.status = AgentStatus.IDLE
        return

    energy_before_resting = agent.energy
    agent.status = AgentStatus.RESTING
    agent.energy = min(max(agent.energy + RESTING_ENERGY_RECOVERY, 0), 100)
    energy_recovered = agent.energy - energy_before_resting
    record_event(
        world,
        EventType.RESTED,
        agent,
        (
            f"Tick {world.current_tick}: {agent.name} rested and "
            f"recovered {energy_recovered} energy."
        ),
    )


def perform_farm_work(agent: Agent, world: World) -> bool:
    location = next(
        (
            location
            for location in world.locations
            if location.id == agent.location_id
        ),
        None,
    )

    rejection_reason = None
    if agent.occupation != Occupation.FARMER:
        rejection_reason = "they are not a farmer"
    elif location is None:
        rejection_reason = "their location does not exist"
    elif location.location_type != LocationType.FARM:
        rejection_reason = "they are not located at a farm"
    elif agent.health <= 0:
        rejection_reason = "they are not healthy enough to act"
    elif agent.energy < FARM_WORK_ENERGY_COST:
        rejection_reason = "they lacked enough energy"
    elif agent.status not in FARM_WORK_ALLOWED_STATUSES:
        rejection_reason = f"their status was {agent.status.value}"

    if rejection_reason is not None:
        record_event(
            world,
            EventType.FARM_WORK_REJECTED,
            agent,
            (
                f"Tick {world.current_tick}: {agent.name} failed to work "
                f"at the farm because {rejection_reason}."
            ),
        )
        return False

    current_food = max(agent.inventory.get(ResourceType.FOOD, 0), 0)
    agent.inventory[ResourceType.FOOD] = current_food + FARM_WORK_FOOD_YIELD
    agent.energy = max(agent.energy - FARM_WORK_ENERGY_COST, 0)
    agent.money = max(agent.money, 0) + FARM_WORK_WAGE
    agent.status = AgentStatus.WORKING
    record_event(
        world,
        EventType.FARM_WORK_SUCCEEDED,
        agent,
        (
            f"Tick {world.current_tick}: {agent.name} produced "
            f"{FARM_WORK_FOOD_YIELD} food at {location.name}."
        ),
    )
    record_event(
        world,
        EventType.WAGE_EARNED,
        agent,
        (
            f"Tick {world.current_tick}: {agent.name} earned "
            f"{FARM_WORK_WAGE} money from farm work."
        ),
    )
    return True


def reject_food_purchase(agent: Agent, world: World, reason: str) -> bool:
    record_event(
        world,
        EventType.FOOD_PURCHASE_REJECTED,
        agent,
        (
            f"Tick {world.current_tick}: {agent.name} failed to purchase "
            f"food because {reason}."
        ),
    )
    return False


def purchase_food(agent: Agent, world: World, quantity: int) -> bool:
    if (
        not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity <= 0
    ):
        return reject_food_purchase(agent, world, "the quantity was invalid")

    market = next(
        (
            location
            for location in world.locations
            if location.id == agent.location_id
        ),
        None,
    )
    if market is None:
        return reject_food_purchase(
            agent,
            world,
            "their location does not exist",
        )
    if market.location_type != LocationType.MARKET:
        return reject_food_purchase(
            agent,
            world,
            "they were not located at a market",
        )

    buyer_food = agent.inventory.get(ResourceType.FOOD, 0)
    market_food = market.inventory.get(ResourceType.FOOD, 0)
    total_price = quantity * MARKET_FOOD_UNIT_PRICE

    if agent.money < 0:
        return reject_food_purchase(
            agent,
            world,
            "their money balance was invalid",
        )
    if buyer_food < 0:
        return reject_food_purchase(
            agent,
            world,
            "their food inventory was invalid",
        )
    if market_food < 0:
        return reject_food_purchase(
            agent,
            world,
            "the market stock was invalid",
        )
    if agent.money < total_price:
        return reject_food_purchase(agent, world, "they lacked money")
    if market_food < quantity:
        return reject_food_purchase(
            agent,
            world,
            "the market lacked enough food",
        )

    agent.money -= total_price
    agent.inventory[ResourceType.FOOD] = buyer_food + quantity
    market.inventory[ResourceType.FOOD] = market_food - quantity
    record_event(
        world,
        EventType.FOOD_PURCHASED,
        agent,
        (
            f"Tick {world.current_tick}: {agent.name} purchased "
            f"{quantity} food from {market.name} for {total_price} money."
        ),
    )
    return True


def advance_tick(world: World) -> World:
    world.current_tick += 1

    for agent in world.agents:
        agent.hunger = min(agent.hunger + 2, 100)
        agent.energy = max(agent.energy - 1, 0)
        apply_automatic_eating(agent, world)
        apply_automatic_resting(agent, world)

    return world
