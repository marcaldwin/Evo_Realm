import asyncio
from copy import deepcopy

from backend.app.core.enums import WorldStatus
from backend.app.services.world_service import WorldStepResult
from backend.app.simulation.models import World
from backend.app.simulation.runtime import SimulationRuntime


def build_result(tick: int) -> WorldStepResult:
    previous_world = World(
        id="world-1",
        name="Runtime World",
        current_tick=tick,
        seed=42,
        status=WorldStatus.RUNNING,
        locations=[],
        agents=[],
    )
    updated_world = deepcopy(previous_world)
    updated_world.current_tick += 1
    return WorldStepResult(previous_world, updated_world)


def test_runtime_starts_only_one_task_and_stops_cleanly() -> None:
    published_ticks: list[int] = []
    next_tick = 0
    published_twice = asyncio.Event()

    def step_world(_: str) -> WorldStepResult:
        nonlocal next_tick
        result = build_result(next_tick)
        next_tick += 1
        return result

    async def publish(result: WorldStepResult) -> None:
        published_ticks.append(result.updated_world.current_tick)
        if len(published_ticks) >= 2:
            published_twice.set()

    async def exercise_runtime() -> None:
        runtime = SimulationRuntime(
            0.001,
            step_function=step_world,
            publish_function=publish,
            world_id_loader=lambda: [],
        )

        assert await runtime.start("world-1") is True
        assert await runtime.start("world-1") is False
        await asyncio.wait_for(published_twice.wait(), timeout=1)
        assert runtime.is_running("world-1") is True
        assert await runtime.stop("world-1") is True
        tick_count_after_stop = len(published_ticks)
        await asyncio.sleep(0.01)

        assert len(published_ticks) == tick_count_after_stop
        assert runtime.is_running("world-1") is False

    asyncio.run(exercise_runtime())


def test_runtime_restores_persisted_running_worlds() -> None:
    published = asyncio.Event()

    def step_world(_: str) -> WorldStepResult:
        return build_result(0)

    async def publish(_: WorldStepResult) -> None:
        published.set()

    async def exercise_runtime() -> None:
        runtime = SimulationRuntime(
            0.001,
            step_function=step_world,
            publish_function=publish,
            world_id_loader=lambda: ["world-1"],
        )

        await runtime.restore_running_worlds()
        await asyncio.wait_for(published.wait(), timeout=1)

        assert runtime.is_running("world-1") is True

        await runtime.shutdown()

        assert runtime.is_running("world-1") is False

    asyncio.run(exercise_runtime())
