from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from ...realtime.manager import stream_manager
from ...realtime.schemas import SnapshotLoadedMessage
from ...services.world_service import get_world


router = APIRouter()


@router.websocket("/api/worlds/{world_id}/stream")
async def stream_world(
    websocket: WebSocket,
    world_id: str,
) -> None:
    world = await run_in_threadpool(get_world, world_id)
    if world is None:
        await websocket.close(
            code=4404,
            reason="World not found",
        )
        return

    await stream_manager.accept(websocket)

    try:
        ready_event = stream_manager.ready_event(
            world_id=world_id,
            tick=world.current_tick,
        )
        await websocket.send_json(
            ready_event.model_dump(mode="json")
        )

        try:
            SnapshotLoadedMessage.model_validate(
                await websocket.receive_json()
            )
        except ValidationError:
            await websocket.close(
                code=4400,
                reason="Invalid snapshot acknowledgement",
            )
            return

        latest_world = await run_in_threadpool(
            get_world,
            world_id,
        )
        if latest_world is None:
            await websocket.close(
                code=4404,
                reason="World not found",
            )
            return

        stream_manager.subscribe(world_id, websocket)
        subscribed_event = stream_manager.subscribed_event(
            world_id=world_id,
            tick=latest_world.current_tick,
        )
        await websocket.send_json(
            subscribed_event.model_dump(mode="json")
        )

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        stream_manager.disconnect(world_id, websocket)
