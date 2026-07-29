from copy import deepcopy
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)
pytestmark = pytest.mark.usefixtures("database_world_store")


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
    assert world["status"] == "created"
    assert world["locations"] == valid_world_payload["locations"]
    assert world["agents"][0] == {
        **valid_world_payload["agents"][0],
        "personality_traits": {},
        "active_goal": None,
    }
    assert world["agents"][1] == {
        **valid_world_payload["agents"][1],
        "status": "idle",
        "inventory": {},
        "personality_traits": {},
        "active_goal": None,
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


def test_created_world_can_be_retrieved_by_id(
    valid_world_payload: dict,
) -> None:
    create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    created_world = create_response.json()

    get_response = client.get(f"/api/worlds/{created_world['id']}")

    assert create_response.status_code == 201
    assert get_response.status_code == 200
    assert get_response.json() == created_world


def test_get_world_returns_not_found_for_unknown_id() -> None:
    unknown_world_id = "00000000-0000-4000-8000-000000000000"

    response = client.get(f"/api/worlds/{unknown_world_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}


def test_list_worlds_returns_empty_list_when_none_exist() -> None:
    response = client.get("/api/worlds")

    assert response.status_code == 200
    assert response.json() == []


def test_list_worlds_returns_summaries_without_full_details(
    valid_world_payload: dict,
) -> None:
    second_payload = deepcopy(valid_world_payload)
    second_payload["name"] = "Second World"
    second_payload["seed"] = 99
    second_payload["starting_tick"] = 12

    first_create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    second_create_response = client.post(
        "/api/worlds",
        json=second_payload,
    )

    response = client.get("/api/worlds")

    assert first_create_response.status_code == 201
    assert second_create_response.status_code == 201
    assert response.status_code == 200
    summaries = response.json()
    assert summaries == [
        {
            "id": first_create_response.json()["id"],
            "name": "New Haven",
                "current_tick": 7,
                "seed": 42,
                "status": "created",
                "agent_count": 2,
        },
        {
            "id": second_create_response.json()["id"],
            "name": "Second World",
                "current_tick": 12,
                "seed": 99,
                "status": "created",
                "agent_count": 2,
        },
    ]
    assert all("agents" not in summary for summary in summaries)
    assert all("locations" not in summary for summary in summaries)


def test_step_world_advances_exactly_one_tick_and_saves_state(
    valid_world_payload: dict,
) -> None:
    create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    created_world = create_response.json()
    world_id = created_world["id"]

    step_response = client.post(f"/api/worlds/{world_id}/step")
    get_response = client.get(f"/api/worlds/{world_id}")

    assert create_response.status_code == 201
    assert step_response.status_code == 200
    stepped_world = step_response.json()
    assert stepped_world["current_tick"] == 8
    assert stepped_world["agents"][0]["hunger"] == 22
    assert stepped_world["agents"][0]["energy"] == 89
    assert stepped_world["agents"][1]["hunger"] == 32
    assert stepped_world["agents"][1]["energy"] == 79
    assert get_response.status_code == 200
    assert get_response.json() == stepped_world


def test_each_step_request_advances_only_one_tick(
    valid_world_payload: dict,
) -> None:
    create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    world_id = create_response.json()["id"]

    first_step_response = client.post(f"/api/worlds/{world_id}/step")
    second_step_response = client.post(f"/api/worlds/{world_id}/step")

    assert first_step_response.json()["current_tick"] == 8
    assert second_step_response.json()["current_tick"] == 9


def test_step_world_returns_not_found_for_unknown_id() -> None:
    unknown_world_id = "00000000-0000-4000-8000-000000000000"

    response = client.post(f"/api/worlds/{unknown_world_id}/step")

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}


def test_list_world_agents_returns_validated_summaries(
    valid_world_payload: dict,
) -> None:
    create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    world_id = create_response.json()["id"]

    response = client.get(f"/api/worlds/{world_id}/agents")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == [
        valid_world_payload["agents"][0],
        {
            **valid_world_payload["agents"][1],
            "status": "idle",
            "inventory": {},
        },
    ]


def test_list_world_agents_returns_empty_list_for_world_without_agents(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["agents"] = []
    create_response = client.post("/api/worlds", json=payload)
    world_id = create_response.json()["id"]

    response = client.get(f"/api/worlds/{world_id}/agents")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == []


def test_list_world_agents_returns_not_found_for_unknown_world() -> None:
    unknown_world_id = "00000000-0000-4000-8000-000000000000"

    response = client.get(f"/api/worlds/{unknown_world_id}/agents")

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}


def test_get_world_agent_returns_inspector_snapshot(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["agents"][0]["personality_traits"] = {
        "curiosity": 70,
        "cooperation": 45,
    }
    payload["agents"][0]["active_goal"] = "Grow food reserves"
    create_response = client.post("/api/worlds", json=payload)
    world_id = create_response.json()["id"]

    response = client.get(
        f"/api/worlds/{world_id}/agents/agent-1"
    )

    assert response.status_code == 200
    assert response.json() == {
        **payload["agents"][0],
        "recent_actions": [],
        "selected_retrieved_memories": [],
    }


def test_get_world_agent_returns_not_found_for_missing_agent(
    valid_world_payload: dict,
) -> None:
    create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    world_id = create_response.json()["id"]

    response = client.get(
        f"/api/worlds/{world_id}/agents/missing-agent"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Agent not found"}


def test_list_world_events_returns_events_created_by_step(
    valid_world_payload: dict,
) -> None:
    payload = deepcopy(valid_world_payload)
    payload["agents"][0]["hunger"] = 68
    create_response = client.post("/api/worlds", json=payload)
    world_id = create_response.json()["id"]

    step_response = client.post(f"/api/worlds/{world_id}/step")
    response = client.get(f"/api/worlds/{world_id}/events")

    assert create_response.status_code == 201
    assert step_response.status_code == 200
    assert response.status_code == 200
    assert response.json() == [
        {
            "tick": 8,
            "event_type": "food_consumed",
            "agent_id": "agent-1",
            "location_id": "farm-1",
            "summary": (
                "Tick 8: Elena consumed 1 food and reduced hunger by 30."
            ),
        }
    ]


def test_list_world_events_returns_empty_list_when_no_events_exist(
    valid_world_payload: dict,
) -> None:
    create_response = client.post(
        "/api/worlds",
        json=valid_world_payload,
    )
    world_id = create_response.json()["id"]

    response = client.get(f"/api/worlds/{world_id}/events")

    assert create_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == []


def test_list_world_events_returns_not_found_for_unknown_world() -> None:
    unknown_world_id = "00000000-0000-4000-8000-000000000000"

    response = client.get(f"/api/worlds/{unknown_world_id}/events")

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}


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


def test_world_endpoints_appear_in_openapi() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "post" in paths["/api/worlds"]
    assert "get" in paths["/api/worlds"]
    assert "get" in paths["/api/worlds/{world_id}"]
    assert "post" in paths["/api/worlds/{world_id}/step"]
    assert "post" in paths["/api/worlds/{world_id}/start"]
    assert "post" in paths["/api/worlds/{world_id}/pause"]
    assert "post" in paths["/api/worlds/{world_id}/resume"]
    assert "get" in paths["/api/worlds/{world_id}/agents"]
    assert "get" in paths[
        "/api/worlds/{world_id}/agents/{agent_id}"
    ]
    assert "get" in paths["/api/worlds/{world_id}/events"]
