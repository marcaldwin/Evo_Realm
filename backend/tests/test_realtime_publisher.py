import asyncio
from copy import deepcopy
from typing import Any, cast

from backend.app.core.enums import (
    AgentStatus,
    DialogueAct,
    EventType,
    LocationType,
    Occupation,
    StreamEventType,
)
from backend.app.memory.schemas import EpisodicMemory
from backend.app.realtime.manager import LiveStreamManager
from backend.app.realtime.publisher import (
    publish_conversation_message,
    publish_memory_created,
    publish_relationship_change,
    publish_world_step,
)
from backend.app.services.world_service import WorldStepResult
from backend.app.simulation.models import (
    Agent,
    Location,
    SimulationEvent,
    World,
)
from backend.app.social.schemas import (
    ConversationTurn,
    DirectionalRelationship,
)


class RecordingManager:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def broadcast(self, **event: Any) -> None:
        self.events.append(event)


def manager_for_test() -> tuple[RecordingManager, LiveStreamManager]:
    recording_manager = RecordingManager()
    return recording_manager, cast(
        LiveStreamManager,
        recording_manager,
    )


def test_world_step_publishes_changes_and_events_in_order() -> None:
    previous_world = World(
        id="world-1",
        name="Realtime World",
        current_tick=4,
        seed=42,
        locations=[
            Location(
                id="home",
                name="Home",
                location_type=LocationType.HOME,
                x=0,
                y=0,
                capacity=5,
            ),
            Location(
                id="farm",
                name="Farm",
                location_type=LocationType.FARM,
                x=1,
                y=0,
                capacity=5,
            ),
        ],
        agents=[
            Agent(
                id="elena",
                name="Elena",
                occupation=Occupation.FARMER,
                location_id="home",
                status=AgentStatus.IDLE,
                hunger=10,
                energy=100,
                health=100,
                money=5,
            )
        ],
    )
    updated_world = deepcopy(previous_world)
    updated_world.current_tick = 5
    updated_world.agents[0].location_id = "farm"
    updated_world.agents[0].hunger = 12
    updated_world.events.extend(
        [
            SimulationEvent(
                tick=5,
                event_type=EventType.RESTED,
                agent_id="elena",
                location_id="farm",
                summary="Elena rested.",
            ),
            SimulationEvent(
                tick=5,
                event_type=EventType.FARM_WORK_REJECTED,
                agent_id="elena",
                location_id="farm",
                summary="Elena could not work.",
            ),
        ]
    )
    recording, manager = manager_for_test()

    asyncio.run(
        publish_world_step(
            WorldStepResult(previous_world, updated_world),
            manager=manager,
        )
    )

    assert [
        event["event_type"]
        for event in recording.events
    ] == [
        StreamEventType.TICK_COMMITTED,
        StreamEventType.AGENT_MOVED,
        StreamEventType.AGENT_STATE_CHANGED,
        StreamEventType.ACTION_EXECUTED,
        StreamEventType.WORLD_EVENT,
        StreamEventType.ACTION_REJECTED,
        StreamEventType.WORLD_EVENT,
    ]
    assert recording.events[1]["payload"] == {
        "agent_id": "elena",
        "from_location_id": "home",
        "to_location_id": "farm",
    }
    assert recording.events[2]["payload"]["changes"]["hunger"] == {
        "before": 10,
        "after": 12,
    }


def test_conversation_relationship_and_memory_publishers() -> None:
    recording, manager = manager_for_test()
    turn = ConversationTurn(
        turn_id="turn-1",
        conversation_id="conversation-1",
        turn_number=1,
        speaker_agent_id="elena",
        listener_agent_id="marco",
        dialogue_act=DialogueAct.INFORM,
        message="The farm needs help.",
        creation_tick=8,
    )
    previous_relationship = DirectionalRelationship(
        relationship_id="relationship-1",
        world_id="world-1",
        source_agent_id="elena",
        target_agent_id="marco",
        trust=2,
        interaction_count=1,
    )
    updated_relationship = previous_relationship.model_copy(
        update={
            "trust": 5,
            "interaction_count": 2,
        }
    )
    memory = EpisodicMemory(
        memory_id="memory-1",
        world_id="world-1",
        owner_agent_id="elena",
        content="Marco helped at the farm.",
        importance=0.8,
        emotional_value=0.5,
        creation_tick=8,
        source_event_sequence=12,
        source_agent_id="marco",
        embedding=(0.1, 0.2),
        embedding_model="test-embedding",
        embedding_dimensions=2,
    )

    async def publish_events() -> None:
        await publish_conversation_message(
            world_id="world-1",
            tick=8,
            turn=turn,
            manager=manager,
        )
        await publish_relationship_change(
            tick=8,
            previous=previous_relationship,
            updated=updated_relationship,
            manager=manager,
        )
        await publish_memory_created(
            memory,
            manager=manager,
        )

    asyncio.run(publish_events())

    assert [
        event["event_type"]
        for event in recording.events
    ] == [
        StreamEventType.CONVERSATION_MESSAGE,
        StreamEventType.RELATIONSHIP_CHANGED,
        StreamEventType.MEMORY_CREATED,
    ]
    assert recording.events[0]["payload"]["dialogue_act"] == "inform"
    assert recording.events[1]["payload"]["changes"] == {
        "trust": {"before": 2, "after": 5},
        "interaction_count": {"before": 1, "after": 2},
    }
    memory_payload = recording.events[2]["payload"]
    assert memory_payload["memory_id"] == "memory-1"
    assert "embedding" not in memory_payload
