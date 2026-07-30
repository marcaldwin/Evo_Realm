import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.main import app


client = TestClient(app)
pytestmark = pytest.mark.usefixtures("database_world_store")


def test_stream_rejects_unknown_world() -> None:
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(
            "/api/worlds/missing-world/stream"
        ):
            pass

    assert error.value.code == 4404
    assert error.value.reason == "World not found"


def create_world() -> dict:
    response = client.post(
        "/api/worlds",
        json={
            "name": "Stream World",
            "seed": 42,
            "locations": [
                {
                    "id": "home",
                    "name": "Home",
                    "location_type": "home",
                    "x": 0,
                    "y": 0,
                    "capacity": 5,
                }
            ],
            "agents": [
                {
                    "id": "elena",
                    "name": "Elena",
                    "occupation": "farmer",
                    "location_id": "home",
                    "status": "idle",
                    "hunger": 10,
                    "energy": 100,
                    "health": 100,
                    "money": 5,
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_stream_receives_ordered_committed_tick_updates() -> None:
    world = create_world()
    world_id = world["id"]

    with client.websocket_connect(
        f"/api/worlds/{world_id}/stream"
    ) as websocket:
        ready = websocket.receive_json()

        assert ready["version"] == "1.0"
        assert ready["sequence"] == 0
        assert ready["world_id"] == world_id
        assert ready["tick"] == 0
        assert ready["event_type"] == "stream_ready"
        assert ready["payload"]["snapshot_required"] is True
        assert ready["timestamp"]

        websocket.send_json(
            {
                "type": "snapshot_loaded",
                "snapshot_tick": 0,
            }
        )
        subscribed = websocket.receive_json()

        assert subscribed["event_type"] == "stream_ready"
        assert subscribed["payload"] == {
            "snapshot_required": False,
            "subscribed": True,
        }

        step_response = client.post(
            f"/api/worlds/{world_id}/step"
        )
        tick_event = websocket.receive_json()
        state_event = websocket.receive_json()

    assert step_response.status_code == 200
    assert step_response.json()["current_tick"] == 1

    assert tick_event["event_type"] == "tick_committed"
    assert tick_event["tick"] == 1
    assert tick_event["sequence"] == 1
    assert tick_event["payload"]["previous_tick"] == 0
    assert tick_event["payload"]["current_tick"] == 1

    assert state_event["event_type"] == "agent_state_changed"
    assert state_event["tick"] == 1
    assert state_event["sequence"] == 2
    assert state_event["payload"]["agent_id"] == "elena"
    assert state_event["payload"]["changes"]["hunger"] == {
        "before": 10,
        "after": 12,
    }


def test_reconnect_requires_fresh_snapshot_before_new_events() -> None:
    world = create_world()
    world_id = world["id"]

    with client.websocket_connect(
        f"/api/worlds/{world_id}/stream"
    ) as first_socket:
        first_ready = first_socket.receive_json()
        first_socket.send_json(
            {
                "type": "snapshot_loaded",
                "snapshot_tick": first_ready["tick"],
            }
        )
        first_socket.receive_json()

        first_step = client.post(
            f"/api/worlds/{world_id}/step"
        )
        first_tick_event = first_socket.receive_json()
        first_socket.receive_json()

    assert first_step.status_code == 200
    assert first_tick_event["sequence"] == 1

    disconnected_step = client.post(
        f"/api/worlds/{world_id}/step"
    )
    assert disconnected_step.status_code == 200
    assert disconnected_step.json()["current_tick"] == 2

    with client.websocket_connect(
        f"/api/worlds/{world_id}/stream"
    ) as second_socket:
        reconnect_ready = second_socket.receive_json()

        assert reconnect_ready["tick"] == 2
        assert reconnect_ready["sequence"] == 4
        assert reconnect_ready["payload"]["snapshot_required"] is True

        second_socket.send_json(
            {
                "type": "snapshot_loaded",
                "snapshot_tick": reconnect_ready["tick"],
            }
        )
        subscribed = second_socket.receive_json()

        assert subscribed["tick"] == 2
        assert subscribed["payload"]["subscribed"] is True

        third_step = client.post(
            f"/api/worlds/{world_id}/step"
        )
        next_tick_event = second_socket.receive_json()

    assert third_step.status_code == 200
    assert next_tick_event["event_type"] == "tick_committed"
    assert next_tick_event["sequence"] == 5
    assert next_tick_event["tick"] == 3


def test_stream_subscribes_when_world_advances_during_handshake() -> None:
    world = create_world()
    world_id = world["id"]

    with client.websocket_connect(
        f"/api/worlds/{world_id}/stream"
    ) as websocket:
        ready = websocket.receive_json()
        step_response = client.post(
            f"/api/worlds/{world_id}/step"
        )

        websocket.send_json(
            {
                "type": "snapshot_loaded",
                "snapshot_tick": ready["tick"],
            }
        )
        subscribed = websocket.receive_json()

    assert step_response.status_code == 200
    assert subscribed["tick"] == 1
    assert subscribed["payload"] == {
        "snapshot_required": False,
        "subscribed": True,
    }
