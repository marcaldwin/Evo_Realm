from asyncio import Lock
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import JsonValue

from ..core.enums import StreamEventType
from .schemas import StreamEventEnvelope


class LiveStreamManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._sequences: dict[str, int] = {}
        self._locks: dict[str, Lock] = {}

    async def accept(self, websocket: WebSocket) -> None:
        await websocket.accept()

    def subscribe(
        self,
        world_id: str,
        websocket: WebSocket,
    ) -> None:
        connections = self._connections.setdefault(world_id, set())
        connections.add(websocket)

    def disconnect(
        self,
        world_id: str,
        websocket: WebSocket,
    ) -> None:
        connections = self._connections.get(world_id)
        if connections is None:
            return

        connections.discard(websocket)
        if not connections:
            del self._connections[world_id]

    def current_sequence(self, world_id: str) -> int:
        return self._sequences.get(world_id, 0)

    def connection_count(self, world_id: str) -> int:
        return len(self._connections.get(world_id, set()))

    def ready_event(
        self,
        *,
        world_id: str,
        tick: int,
    ) -> StreamEventEnvelope:
        return StreamEventEnvelope(
            sequence=self.current_sequence(world_id),
            world_id=world_id,
            tick=tick,
            event_type=StreamEventType.STREAM_READY,
            timestamp=datetime.now(timezone.utc),
            payload={
                "snapshot_required": True,
                "snapshot_url": f"/api/worlds/{world_id}",
            },
        )

    def subscribed_event(
        self,
        *,
        world_id: str,
        tick: int,
    ) -> StreamEventEnvelope:
        return StreamEventEnvelope(
            sequence=self.current_sequence(world_id),
            world_id=world_id,
            tick=tick,
            event_type=StreamEventType.STREAM_READY,
            timestamp=datetime.now(timezone.utc),
            payload={
                "snapshot_required": False,
                "subscribed": True,
            },
        )

    async def broadcast(
        self,
        *,
        world_id: str,
        tick: int,
        event_type: StreamEventType,
        payload: dict[str, JsonValue],
    ) -> StreamEventEnvelope:
        lock = self._locks.setdefault(world_id, Lock())

        async with lock:
            sequence = self.current_sequence(world_id) + 1
            self._sequences[world_id] = sequence
            envelope = StreamEventEnvelope(
                sequence=sequence,
                world_id=world_id,
                tick=tick,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                payload=payload,
            )

            disconnected: list[WebSocket] = []
            for websocket in tuple(
                self._connections.get(world_id, set())
            ):
                try:
                    await websocket.send_json(
                        envelope.model_dump(mode="json")
                    )
                except (
                    OSError,
                    RuntimeError,
                    WebSocketDisconnect,
                ):
                    disconnected.append(websocket)

            for websocket in disconnected:
                self.disconnect(world_id, websocket)

            return envelope


stream_manager = LiveStreamManager()
