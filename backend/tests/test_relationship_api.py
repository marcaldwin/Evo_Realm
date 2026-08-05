import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.social.repository import SocialRepository


client = TestClient(app)
pytestmark = pytest.mark.usefixtures("database_world_store")


def create_world() -> dict:
    response = client.post(
        "/api/worlds",
        json={
            "name": "Relationship World",
            "seed": 42,
            "locations": [
                {
                    "id": "home",
                    "name": "Home",
                    "location_type": "home",
                    "x": 0,
                    "y": 0,
                    "capacity": 2,
                }
            ],
            "agents": [
                {
                    "id": "elena",
                    "name": "Elena",
                    "occupation": "farmer",
                    "location_id": "home",
                    "hunger": 10,
                    "energy": 90,
                    "health": 100,
                    "money": 5,
                },
                {
                    "id": "marco",
                    "name": "Marco",
                    "occupation": "merchant",
                    "location_id": "home",
                    "hunger": 20,
                    "energy": 80,
                    "health": 95,
                    "money": 20,
                },
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_world_relationships_return_directional_values(
    test_session_factory: sessionmaker,
) -> None:
    world = create_world()

    with test_session_factory.begin() as session:
        repository = SocialRepository(session)
        source = repository.get_agent(world["id"], "elena")
        target = repository.get_agent(world["id"], "marco")
        assert source is not None
        assert target is not None
        record = repository.get_or_create_relationship(
            world_database_id=source.record.world_database_id,
            source_agent=source.record,
            target_agent=target.record,
        )
        record.trust = 15
        record.affection = -4
        record.respect = 9
        record.interaction_count = 3
        relationship_id = record.id

    response = client.get(
        f"/api/worlds/{world['id']}/relationships"
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "relationship_id": relationship_id,
            "world_id": world["id"],
            "source_agent_id": "elena",
            "target_agent_id": "marco",
            "trust": 15,
            "affection": -4,
            "respect": 9,
            "interaction_count": 3,
        }
    ]


def test_world_without_relationships_returns_empty_list() -> None:
    world = create_world()

    response = client.get(
        f"/api/worlds/{world['id']}/relationships"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_world_relationships_return_not_found() -> None:
    response = client.get(
        "/api/worlds/missing-world/relationships"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}
