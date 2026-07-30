import pytest

from backend.app.api.schemas.world import WorldCreate
from backend.app.simulation import seed_api
from backend.app.simulation.runner import create_demo_world
from backend.app.simulation.seed_api import (
    seed_demo_world,
    serialize_world_creation_payload,
)


def test_demo_world_serializes_to_valid_world_creation_payload() -> None:
    world = create_demo_world(seed=42)

    payload = serialize_world_creation_payload(world)
    configuration = WorldCreate.model_validate(payload)

    assert configuration.name == world.name
    assert configuration.seed == world.seed
    assert configuration.starting_tick == 0
    assert len(configuration.locations) == 7
    assert {
        location.location_type.value
        for location in configuration.locations
    } == {
        "home",
        "farm",
        "market",
        "clinic",
        "workshop",
        "town_hall",
    }
    clinic = next(
        location
        for location in configuration.locations
        if location.id == "community-clinic"
    )
    assert clinic.inventory == {"medicine": 20}


def test_seed_demo_world_reuses_matching_world(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[tuple[str, str]] = []

    def fake_request(
        method: str,
        url: str,
        payload: dict[str, object] | None = None,
    ) -> object:
        requests.append((method, url))
        assert payload is None
        return [
            {
                "id": "existing-world-id",
                "name": "EvoRealm Demo World",
                "seed": 42,
            }
        ]

    monkeypatch.setattr(seed_api, "_request_json", fake_request)

    result = seed_demo_world(
        seed=42,
        api_base_url="http://localhost:8000/",
    )

    assert result.created is False
    assert result.world_id == "existing-world-id"
    assert requests == [
        ("GET", "http://localhost:8000/api/worlds")
    ]


def test_seed_demo_world_creates_world_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[
        tuple[str, str, dict[str, object] | None]
    ] = []

    def fake_request(
        method: str,
        url: str,
        payload: dict[str, object] | None = None,
    ) -> object:
        requests.append((method, url, payload))
        if method == "GET":
            return []
        return {"id": "created-world-id"}

    monkeypatch.setattr(seed_api, "_request_json", fake_request)

    result = seed_demo_world(
        seed=42,
        api_base_url="http://localhost:8000",
    )

    assert result.created is True
    assert result.world_id == "created-world-id"
    assert requests[0] == (
        "GET",
        "http://localhost:8000/api/worlds",
        None,
    )
    assert requests[1][0:2] == (
        "POST",
        "http://localhost:8000/api/worlds",
    )
    assert requests[1][2] == serialize_world_creation_payload(
        create_demo_world(seed=42)
    )
