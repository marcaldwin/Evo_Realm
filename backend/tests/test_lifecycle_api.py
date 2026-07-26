import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from backend.app.core.enums import WorldStatus
from backend.app.main import app
from backend.app.repositories.world_repository import WorldRepository


client = TestClient(app)
pytestmark = pytest.mark.usefixtures("database_world_store")


def create_world() -> dict:
    response = client.post(
        "/api/worlds",
        json={
            "name": "Lifecycle World",
            "seed": 42,
            "locations": [
                {
                    "id": "home-1",
                    "name": "Central Home",
                    "location_type": "home",
                    "x": 0,
                    "y": 0,
                    "capacity": 1,
                }
            ],
            "agents": [],
        },
    )
    assert response.status_code == 201
    return response.json()


def apply_actions(world_id: str, actions: list[str]) -> None:
    for action in actions:
        response = client.post(f"/api/worlds/{world_id}/{action}")
        assert response.status_code == 200


def test_world_moves_through_valid_lifecycle_and_persists(
    test_session_factory: sessionmaker,
) -> None:
    world = create_world()
    world_id = world["id"]

    start_response = client.post(f"/api/worlds/{world_id}/start")
    pause_response = client.post(f"/api/worlds/{world_id}/pause")
    resume_response = client.post(f"/api/worlds/{world_id}/resume")

    assert world["status"] == "created"
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "running"
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "paused"
    assert resume_response.status_code == 200
    assert resume_response.json()["status"] == "running"

    with test_session_factory() as session:
        restored_world = WorldRepository(session).get(world_id)

    assert restored_world is not None
    assert restored_world.status == WorldStatus.RUNNING


@pytest.mark.parametrize("action", ["start", "pause", "resume"])
def test_lifecycle_operations_return_not_found_for_unknown_world(
    action: str,
) -> None:
    world_id = "00000000-0000-4000-8000-000000000000"

    response = client.post(f"/api/worlds/{world_id}/{action}")

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}


@pytest.mark.parametrize(
    ("setup_actions", "action", "current_status"),
    [
        ([], "pause", "created"),
        ([], "resume", "created"),
        (["start"], "resume", "running"),
        (["start", "pause"], "start", "paused"),
        (["start", "pause"], "pause", "paused"),
    ],
)
def test_invalid_lifecycle_transitions_return_conflict(
    setup_actions: list[str],
    action: str,
    current_status: str,
) -> None:
    world_id = create_world()["id"]
    apply_actions(world_id, setup_actions)

    response = client.post(f"/api/worlds/{world_id}/{action}")
    get_response = client.get(f"/api/worlds/{world_id}")

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            f"Cannot {action} world while status is "
            f"{current_status}."
        )
    }
    assert get_response.status_code == 200
    assert get_response.json()["status"] == current_status


def test_starting_running_world_twice_returns_conflict() -> None:
    world_id = create_world()["id"]

    first_response = client.post(f"/api/worlds/{world_id}/start")
    second_response = client.post(f"/api/worlds/{world_id}/start")
    get_response = client.get(f"/api/worlds/{world_id}")

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "running"
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Cannot start world while status is running."
    }
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "running"
