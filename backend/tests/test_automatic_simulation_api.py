from time import monotonic, sleep

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.simulation.runtime import simulation_runtime


pytestmark = pytest.mark.usefixtures("database_world_store")


def create_world(client: TestClient) -> dict:
    response = client.post(
        "/api/worlds",
        json={
            "name": "Automatic Movement World",
            "seed": 42,
            "locations": [
                {
                    "id": "home",
                    "name": "Home",
                    "location_type": "home",
                    "x": 0,
                    "y": 0,
                    "capacity": 2,
                },
                {
                    "id": "market",
                    "name": "Market",
                    "location_type": "market",
                    "x": 1,
                    "y": 0,
                    "capacity": 2,
                },
            ],
            "agents": [
                {
                    "id": "elena",
                    "name": "Elena",
                    "occupation": "farmer",
                    "location_id": "home",
                    "hunger": 20,
                    "energy": 90,
                    "health": 100,
                    "money": 5,
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def wait_for_tick(
    client: TestClient,
    world_id: str,
    minimum_tick: int,
) -> dict:
    deadline = monotonic() + 2

    while monotonic() < deadline:
        response = client.get(f"/api/worlds/{world_id}")
        assert response.status_code == 200
        world = response.json()
        if world["current_tick"] >= minimum_tick:
            return world
        sleep(0.01)

    raise AssertionError(
        f"World did not reach tick {minimum_tick} before timeout."
    )


def test_start_pause_and_resume_control_automatic_persisted_ticks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        simulation_runtime,
        "tick_interval_seconds",
        0.03,
    )

    with TestClient(app) as client:
        created_world = create_world(client)
        world_id = created_world["id"]

        start_response = client.post(f"/api/worlds/{world_id}/start")

        assert start_response.status_code == 200
        assert start_response.json()["status"] == "running"

        running_world = wait_for_tick(client, world_id, 1)

        assert running_world["status"] == "running"
        assert any(
            event["event_type"] == "agent_moved"
            for event in running_world["events"]
        )

        pause_response = client.post(f"/api/worlds/{world_id}/pause")

        assert pause_response.status_code == 200
        paused_tick = pause_response.json()["current_tick"]
        sleep(0.1)

        paused_world = client.get(
            f"/api/worlds/{world_id}"
        ).json()

        assert paused_world["status"] == "paused"
        assert paused_world["current_tick"] == paused_tick

        resume_response = client.post(f"/api/worlds/{world_id}/resume")

        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "running"

        resumed_world = wait_for_tick(
            client,
            world_id,
            paused_tick + 1,
        )

        assert resumed_world["current_tick"] > paused_tick
