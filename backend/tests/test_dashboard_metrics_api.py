from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import (
    ConversationOutcomeRecord,
    ConversationRecord,
    SimulationEventRecord,
    WorldRecord,
)
from backend.app.main import app


client = TestClient(app)
pytestmark = pytest.mark.usefixtures("database_world_store")


def create_world() -> dict:
    response = client.post(
        "/api/worlds",
        json={
            "name": "Metrics World",
            "seed": 42,
            "starting_tick": 3,
            "locations": [
                {
                    "id": "farm",
                    "name": "Farm",
                    "location_type": "farm",
                    "x": 0,
                    "y": 0,
                    "capacity": 2,
                    "inventory": {"food": 10},
                }
            ],
            "agents": [
                {
                    "id": "elena",
                    "name": "Elena",
                    "occupation": "farmer",
                    "location_id": "farm",
                    "hunger": 20,
                    "energy": 80,
                    "health": 100,
                    "money": 5,
                    "inventory": {"food": 2},
                },
                {
                    "id": "marco",
                    "name": "Marco",
                    "occupation": "worker",
                    "location_id": "farm",
                    "hunger": 30,
                    "energy": 70,
                    "health": 80,
                    "money": 3,
                },
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def seed_metric_records(
    world_id: str,
    session_factory: sessionmaker,
) -> None:
    with session_factory.begin() as session:
        world = session.scalar(
            select(WorldRecord).where(WorldRecord.id == world_id)
        )
        assert world is not None
        agents = {agent.id: agent for agent in world.agents}

        active_conversation = ConversationRecord(
            id=str(uuid4()),
            world=world,
            initiator_agent=agents["elena"],
            participant_agent=agents["marco"],
            status="active",
            start_tick=2,
            end_tick=None,
        )
        completed_conversation = ConversationRecord(
            id=str(uuid4()),
            world=world,
            initiator_agent=agents["marco"],
            participant_agent=agents["elena"],
            status="completed",
            start_tick=1,
            end_tick=2,
        )
        session.add_all(
            [active_conversation, completed_conversation]
        )
        session.flush()

        session.add_all(
            [
                ConversationOutcomeRecord(
                    id=str(uuid4()),
                    conversation=active_conversation,
                    outcome_type="successful_trade",
                    actor_agent_database_id=agents["elena"].database_id,
                    target_agent_database_id=agents["marco"].database_id,
                    confirmed=True,
                    confirmation_tick=3,
                    details={},
                    relationship_applied=True,
                ),
                ConversationOutcomeRecord(
                    id=str(uuid4()),
                    conversation=completed_conversation,
                    outcome_type="emergency_help",
                    actor_agent_database_id=agents["marco"].database_id,
                    target_agent_database_id=agents["elena"].database_id,
                    confirmed=True,
                    confirmation_tick=2,
                    details={},
                    relationship_applied=True,
                ),
                ConversationOutcomeRecord(
                    id=str(uuid4()),
                    conversation=active_conversation,
                    outcome_type="successful_trade",
                    actor_agent_database_id=agents["marco"].database_id,
                    target_agent_database_id=agents["elena"].database_id,
                    confirmed=False,
                    confirmation_tick=3,
                    details={},
                    relationship_applied=False,
                ),
                SimulationEventRecord(
                    world=world,
                    sequence=0,
                    tick=3,
                    event_type="food_purchase_rejected",
                    agent_id="marco",
                    location_id="farm",
                    summary="Marco lacked money.",
                ),
                SimulationEventRecord(
                    world=world,
                    sequence=1,
                    tick=3,
                    event_type="food_consumed",
                    agent_id="elena",
                    location_id="farm",
                    summary="Elena consumed food.",
                ),
            ]
        )


def test_dashboard_metrics_return_complete_world_summary(
    test_session_factory: sessionmaker,
) -> None:
    world = create_world()
    seed_metric_records(world["id"], test_session_factory)

    response = client.get(f"/api/worlds/{world['id']}/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "world_id": world["id"],
        "current_tick": 3,
        "status": "created",
        "total_food": 12,
        "average_health": 90.0,
        "successful_trades": 1,
        "emergency_help_events": 1,
        "rejected_actions": 1,
        "active_conversations": 1,
    }


def test_dashboard_metrics_handle_world_without_agents() -> None:
    response = client.post(
        "/api/worlds",
        json={
            "name": "Empty World",
            "seed": 7,
            "locations": [
                {
                    "id": "home",
                    "name": "Home",
                    "location_type": "home",
                    "x": 0,
                    "y": 0,
                    "capacity": 1,
                }
            ],
            "agents": [],
        },
    )
    world_id = response.json()["id"]

    metrics_response = client.get(
        f"/api/worlds/{world_id}/metrics"
    )

    assert metrics_response.status_code == 200
    assert metrics_response.json()["average_health"] == 0.0
    assert metrics_response.json()["total_food"] == 0


def test_dashboard_metrics_return_not_found_for_unknown_world() -> None:
    response = client.get(
        "/api/worlds/00000000-0000-4000-8000-000000000000/metrics"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "World not found"}
