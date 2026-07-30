import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from threading import Lock

from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from ..core.config import get_settings
from ..realtime.publisher import publish_world_step
from ..services.world_service import (
    WorldStepResult,
    list_running_world_ids,
    step_running_world_with_result,
)


StepFunction = Callable[[str], WorldStepResult | None]
PublishFunction = Callable[[WorldStepResult], Awaitable[None]]
WorldIdLoader = Callable[[], list[str]]

logger = logging.getLogger(__name__)


class SimulationRuntime:
    def __init__(
        self,
        tick_interval_seconds: float,
        *,
        step_function: StepFunction = step_running_world_with_result,
        publish_function: PublishFunction = publish_world_step,
        world_id_loader: WorldIdLoader = list_running_world_ids,
    ) -> None:
        self.tick_interval_seconds = tick_interval_seconds
        self._step_function = step_function
        self._publish_function = publish_function
        self._world_id_loader = world_id_loader
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._tasks_lock = Lock()

    def is_running(self, world_id: str) -> bool:
        with self._tasks_lock:
            task = self._tasks.get(world_id)
            return task is not None and not task.done()

    async def start(self, world_id: str) -> bool:
        with self._tasks_lock:
            existing_task = self._tasks.get(world_id)
            if existing_task is not None and not existing_task.done():
                return False

            task = asyncio.create_task(
                self._run_world(world_id),
                name=f"simulation-{world_id}",
            )
            self._tasks[world_id] = task
            return True

    async def stop(self, world_id: str) -> bool:
        with self._tasks_lock:
            task = self._tasks.pop(world_id, None)

        if task is None or task.done():
            return False

        task.cancel()
        if task.get_loop() is asyncio.get_running_loop():
            with suppress(asyncio.CancelledError):
                await task
        return True

    async def restore_running_worlds(self) -> None:
        try:
            world_ids = await run_in_threadpool(self._world_id_loader)
        except SQLAlchemyError:
            logger.exception("Unable to restore running simulations")
            return

        for world_id in world_ids:
            await self.start(world_id)

    async def shutdown(self) -> None:
        with self._tasks_lock:
            world_ids = list(self._tasks)

        for world_id in world_ids:
            await self.stop(world_id)

    async def _run_world(self, world_id: str) -> None:
        current_task = asyncio.current_task()
        try:
            while True:
                await asyncio.sleep(self.tick_interval_seconds)
                result = await run_in_threadpool(
                    self._step_function,
                    world_id,
                )
                if result is None:
                    return
                await self._publish_function(result)
        finally:
            with self._tasks_lock:
                if self._tasks.get(world_id) is current_task:
                    del self._tasks[world_id]


simulation_runtime = SimulationRuntime(
    get_settings().simulation_tick_interval_seconds
)
