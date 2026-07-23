import argparse
from collections import Counter
from collections.abc import Sequence

from ..core.enums import ResourceType
from .models import SimulationEvent, World
from .runner import (
    DEFAULT_SIMULATION_TICKS,
    create_demo_world,
    run_simulation,
    validate_world_state,
)


def calculate_resource_totals(world: World) -> dict[ResourceType, int]:
    totals = {resource_type: 0 for resource_type in ResourceType}

    for location in world.locations:
        for resource_type, quantity in location.inventory.items():
            totals[resource_type] += quantity

    for agent in world.agents:
        for resource_type, quantity in agent.inventory.items():
            totals[resource_type] += quantity

    return totals


def format_initial_world(world: World, ticks: int) -> str:
    locations_by_id = {
        location.id: location
        for location in world.locations
    }
    occupancy = Counter(agent.location_id for agent in world.agents)
    lines = [
        "=== EvoRealm Command-Line Simulation Demo ===",
        f"Seed: {world.seed}",
        f"Planned ticks: {ticks}",
        "",
        "=== Initial World Configuration ===",
        "Locations:",
    ]

    for location in world.locations:
        lines.append(
            f"- {location.name} ({location.location_type.value}) "
            f"at ({location.x}, {location.y}) | "
            f"occupancy {occupancy[location.id]}/{location.capacity} | "
            f"inventory: {_format_inventory(location.inventory)}"
        )

    lines.append("Agents:")
    for agent in world.agents:
        location_name = locations_by_id[agent.location_id].name
        lines.append(
            f"- {agent.name} ({agent.occupation.value}) at {location_name} | "
            f"hunger {agent.hunger}, energy {agent.energy}, "
            f"health {agent.health}, money {agent.money} | "
            f"inventory: {_format_inventory(agent.inventory)}"
        )

    return "\n".join(lines)


def format_event_report(
    events: list[SimulationEvent],
    event_limit: int,
) -> str:
    event_counts = Counter(event.event_type.value for event in events)
    lines = [
        "=== Important Simulation Events ===",
        f"Recorded events: {len(events)}",
    ]

    selected_events, omitted_count = _select_events(events, event_limit)
    if not selected_events:
        lines.append("- No event details requested.")
    else:
        for event in selected_events:
            lines.append(f"- [{event.event_type.value}] {event.summary}")
        if omitted_count:
            lines.append(f"... {omitted_count} events omitted ...")

    lines.extend(["", "Event totals:"])
    for event_type, count in sorted(event_counts.items()):
        lines.append(f"- {event_type}: {count}")

    return "\n".join(lines)


def format_final_report(world: World) -> str:
    locations_by_id = {
        location.id: location
        for location in world.locations
    }
    resource_totals = calculate_resource_totals(world)
    lines = [
        "=== Final Agent States ===",
    ]

    for agent in world.agents:
        location_name = locations_by_id[agent.location_id].name
        lines.append(
            f"- {agent.name}: status {agent.status.value}, "
            f"location {location_name}, hunger {agent.hunger}, "
            f"energy {agent.energy}, health {agent.health}, "
            f"money {agent.money}, "
            f"inventory: {_format_inventory(agent.inventory)}"
        )

    lines.extend(["", "=== Final Resource Totals ==="])
    for resource_type in ResourceType:
        lines.append(
            f"- {resource_type.value}: "
            f"{resource_totals[resource_type]}"
        )
    lines.append(
        f"- agent money balances: "
        f"{sum(agent.money for agent in world.agents)}"
    )

    lines.extend(
        [
            "",
            "=== Invariant Status ===",
            "PASS - all simulation invariants remained valid.",
        ]
    )
    return "\n".join(lines)


def _format_inventory(inventory: dict[ResourceType, int]) -> str:
    if not inventory:
        return "empty"
    return ", ".join(
        f"{resource_type.value}={quantity}"
        for resource_type, quantity in sorted(
            inventory.items(),
            key=lambda item: item[0].value,
        )
    )


def _select_events(
    events: list[SimulationEvent],
    event_limit: int,
) -> tuple[list[SimulationEvent], int]:
    if event_limit == 0:
        return [], len(events)
    if len(events) <= event_limit:
        return events, 0

    selected_indexes = []
    seen_event_types = set()
    for index, event in enumerate(events):
        if event.event_type in seen_event_types:
            continue
        selected_indexes.append(index)
        seen_event_types.add(event.event_type)
        if len(selected_indexes) == event_limit:
            break

    recent_indexes = []
    for index in range(len(events) - 1, -1, -1):
        if len(selected_indexes) + len(recent_indexes) == event_limit:
            break
        if index not in selected_indexes:
            recent_indexes.append(index)

    selected_indexes.extend(reversed(recent_indexes))
    selected_events = [events[index] for index in selected_indexes]
    return selected_events, len(events) - len(selected_events)


def _non_negative_integer(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed_value


def _create_progress_reporter(total_ticks: int):
    progress_interval = max(total_ticks // 10, 1)

    def report_progress(world: World) -> None:
        if (
            world.current_tick == 1
            or world.current_tick % progress_interval == 0
            or world.current_tick == total_ticks
        ):
            print(
                f"Tick {world.current_tick}/{total_ticks} complete "
                f"| events recorded: {len(world.events)}"
            )

    return report_progress


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic EvoRealm simulation demo.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--ticks",
        type=_non_negative_integer,
        default=DEFAULT_SIMULATION_TICKS,
    )
    parser.add_argument(
        "--event-limit",
        type=_non_negative_integer,
        default=12,
        help="Maximum number of event summaries to display.",
    )
    arguments = parser.parse_args(argv)

    world = create_demo_world(arguments.seed)
    print(format_initial_world(world, arguments.ticks))
    print("\n=== Simulation Progress ===")

    try:
        run_simulation(
            world,
            ticks=arguments.ticks,
            on_tick=_create_progress_reporter(arguments.ticks),
        )
        validate_world_state(world)
    except ValueError as error:
        print("\n=== Invariant Status ===")
        print(f"FAIL - {error}")
        return 1

    print()
    print(format_event_report(world.events, arguments.event_limit))
    print()
    print(format_final_report(world))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
