from copy import deepcopy
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


@pytest.fixture
def valid_world_payload() -> dict:
    return {
        "name": "New Haven",
        "seed": 42,
        "starting_tick": 7,
        "locations": [
            {
                "id": "farm-1",
                "name": "North Farm",
                "location_type": "farm",
                "x": 0,
                "y": 0,
                "capacity": 2,
                "inventory": {"food": 10},
            },
            {
                "id": "market-1",
                "name": "Central Market",
                "location_type": "market",
                "x": 5,
                "y": 0,
                "capacity": 3,
                "inventory": {"food": 20},
            },
        ],
        "agents": [
            {
                "id": "agent-1",
                "name": "Elena",
                "occupation": "farmer",
                "location_id": "farm-1",
                "status": "idle",
                "hunger": 20,
                "energy": 90,
                "health": 100,
                "money": 5,
                "inventory": {"food": 2},
            },
            {
                "id": "agent-2",
                "name": "Sofia",
                "occupation": "worker",
                "location_id": "market-1",
                "hunger": 30,
                "energy": 80,
                "health": 95,
                "money": 20,
            },
        ],
    }


def test_create_world_returns_valid_world_state(
    valid_world_payload: dict,
) -> None:
    response = client.post("/api/worlds", json=valid_world_payload)

    assert response.status_code == 201
    world = response.json()
    assert UUID(world["id"]).version == 4
    assert world["name"] == "New Haven"
    assert world["seed"] == 42
    assert world["current_tick"] == 7
    assert world["locations"] == valid_world_payload["locations"]
    assert world["agents"][0] == valid_world_payload["agents"][0]
    assert world["agents"][1] == {
        **valid_world_payload["agents"][1],
        "status": "idle",
        "inventory": {},
    }
    assert world["events"] == []


def test_create_world_generates_unique_world_ids(
    valid_world_payload: dict,
) -> None:
    first_response = client.post("/api/worlds", json=valid_world_payload)
    second_response = client.post("/api/worlds", json=valid_world_payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] != second_response.json()["id"]


@pytest.mark.parametrize("missing_field", ["name", "seed", "locations", "agents"])
def test_create_world_rejects_incomplete_input(
    valid_world_payload: dict,
    missing_field: str,
) -> None:
    payload = deepcopy(valid_world_payload)
    del payload[missing_field]

    response = client.post("/api/worlds", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("starting_tick",), -1),
        (("locations", 0, "capacity"), -1),
        (("locations", 0, "inventory"), {"food": -1}),
        (("agents", 0, "hunger"), 101),
        (("agents", 0, "energy"), -1),
        (("agents", 0, "health"), 101),
        (("agents", 0, "money"), -1),
        (("agents", 0, "inventory"), {"food": -1}),
    ],
)
def test_create_world_rejects_invalid_state_values(
    valid_world_payload: dict,
    path: tuple,
    invalid_value: object,
) -> None:
    payload = deepcopy(valid_world_payload)
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = invalid_value

    response = client.post("/api/worlds", json=payload)

    assert response.status_code == 422


def test_create_world_rejects_duplicate_location_ids(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["locations"][1]["id"] = "farm-1"

    response = client.post("/api/worlds", json=payload)

    assert response.status_code == 422
    assert "Location IDs must be unique" in response.text


def test_create_world_rejects_duplicate_agent_ids(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["agents"][1]["id"] = "agent-1"

    response = client.post("/api/worlds", json=payload)

    assert response.status_code == 422
    assert "Agent IDs must be unique" in response.text


def test_create_world_rejects_unknown_agent_location(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["agents"][0]["location_id"] = "missing-location"

    response = client.post("/api/worlds", json=payload)

    assert response.status_code == 422
    assert "references an unknown location" in response.text


def test_create_world_rejects_exceeded_location_capacity(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["agents"][1]["location_id"] = "farm-1"
    payload["locations"][0]["capacity"] = 1

    response = client.post("/api/worlds", json=payload)

    assert response.status_code == 422
    assert "capacity would be exceeded" in response.text


def test_world_creation_endpoint_appears_in_openapi() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "post" in response.json()["paths"]["/api/worlds"]
