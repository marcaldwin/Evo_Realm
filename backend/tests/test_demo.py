from backend.app.core.enums import ResourceType
from backend.app.simulation.demo import (
    calculate_resource_totals,
    main,
)
from backend.app.simulation.runner import create_demo_world


def test_resource_totals_include_agents_and_locations() -> None:
    world = create_demo_world(seed=42)

    totals = calculate_resource_totals(world)

    assert totals[ResourceType.FOOD] == 106
    assert totals[ResourceType.MEDICINE] == 0
    assert totals[ResourceType.WOOD] == 0
    assert totals[ResourceType.MONEY] == 0


def test_command_line_demo_prints_complete_readable_report(
    capsys,
) -> None:
    exit_code = main(
        [
            "--seed",
            "42",
            "--ticks",
            "10",
            "--event-limit",
            "4",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "=== Initial World Configuration ===" in output
    assert "Tick 10/10 complete" in output
    assert "=== Important Simulation Events ===" in output
    assert "events omitted" in output
    assert "=== Final Agent States ===" in output
    assert "=== Final Resource Totals ===" in output
    assert "PASS - all simulation invariants remained valid." in output


def test_command_line_demo_is_deterministic(capsys) -> None:
    arguments = [
        "--seed",
        "7",
        "--ticks",
        "5",
        "--event-limit",
        "2",
    ]

    first_exit_code = main(arguments)
    first_output = capsys.readouterr().out
    second_exit_code = main(arguments)
    second_output = capsys.readouterr().out

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert first_output == second_output
