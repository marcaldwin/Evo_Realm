from pydantic import JsonValue

from ..core.enums import StreamEventType
from ..memory.schemas import EpisodicMemory
from ..services.world_service import WorldStepResult
from ..simulation.models import Agent, SimulationEvent
from ..social.schemas import ConversationTurn, DirectionalRelationship
from .manager import LiveStreamManager, stream_manager


def _inventory_payload(agent: Agent) -> dict[str, int]:
    return {
        resource_type.value: quantity
        for resource_type, quantity in agent.inventory.items()
    }


def _agent_state(agent: Agent) -> dict[str, JsonValue]:
    return {
        "status": agent.status.value,
        "hunger": agent.hunger,
        "energy": agent.energy,
        "health": agent.health,
        "money": agent.money,
        "inventory": _inventory_payload(agent),
    }


def _agent_changes(
    previous: Agent,
    updated: Agent,
) -> dict[str, JsonValue]:
    previous_state = _agent_state(previous)
    updated_state = _agent_state(updated)

    return {
        field: {
            "before": previous_state[field],
            "after": updated_state[field],
        }
        for field in previous_state
        if previous_state[field] != updated_state[field]
    }


def _event_payload(
    event: SimulationEvent,
) -> dict[str, JsonValue]:
    return {
        "source_event_type": event.event_type.value,
        "agent_id": event.agent_id,
        "location_id": event.location_id,
        "summary": event.summary,
    }


async def publish_world_step(
    result: WorldStepResult,
    *,
    manager: LiveStreamManager = stream_manager,
) -> None:
    previous_world = result.previous_world
    updated_world = result.updated_world
    world_id = updated_world.id
    tick = updated_world.current_tick

    await manager.broadcast(
        world_id=world_id,
        tick=tick,
        event_type=StreamEventType.TICK_COMMITTED,
        payload={
            "previous_tick": previous_world.current_tick,
            "current_tick": tick,
            "agent_count": len(updated_world.agents),
            "event_count": len(updated_world.events),
        },
    )

    previous_agents = {
        agent.id: agent
        for agent in previous_world.agents
    }

    for updated_agent in updated_world.agents:
        previous_agent = previous_agents[updated_agent.id]

        if previous_agent.location_id != updated_agent.location_id:
            await manager.broadcast(
                world_id=world_id,
                tick=tick,
                event_type=StreamEventType.AGENT_MOVED,
                payload={
                    "agent_id": updated_agent.id,
                    "from_location_id": previous_agent.location_id,
                    "to_location_id": updated_agent.location_id,
                },
            )

        changes = _agent_changes(previous_agent, updated_agent)
        if changes:
            await manager.broadcast(
                world_id=world_id,
                tick=tick,
                event_type=StreamEventType.AGENT_STATE_CHANGED,
                payload={
                    "agent_id": updated_agent.id,
                    "changes": changes,
                },
            )

    new_events = updated_world.events[
        len(previous_world.events):
    ]
    for event in new_events:
        payload = _event_payload(event)
        action_event_type = (
            StreamEventType.ACTION_REJECTED
            if event.event_type.value.endswith("_rejected")
            else StreamEventType.ACTION_EXECUTED
        )
        await manager.broadcast(
            world_id=world_id,
            tick=tick,
            event_type=action_event_type,
            payload=payload,
        )
        await manager.broadcast(
            world_id=world_id,
            tick=tick,
            event_type=StreamEventType.WORLD_EVENT,
            payload=payload,
        )


async def publish_conversation_message(
    *,
    world_id: str,
    tick: int,
    turn: ConversationTurn,
    manager: LiveStreamManager = stream_manager,
) -> None:
    await manager.broadcast(
        world_id=world_id,
        tick=tick,
        event_type=StreamEventType.CONVERSATION_MESSAGE,
        payload={
            "conversation_id": turn.conversation_id,
            "turn_id": turn.turn_id,
            "turn_number": turn.turn_number,
            "speaker_agent_id": turn.speaker_agent_id,
            "listener_agent_id": turn.listener_agent_id,
            "dialogue_act": turn.dialogue_act.value,
            "message": turn.message,
        },
    )


async def publish_relationship_change(
    *,
    tick: int,
    updated: DirectionalRelationship,
    previous: DirectionalRelationship | None = None,
    manager: LiveStreamManager = stream_manager,
) -> None:
    previous_values = {
        "trust": previous.trust if previous else 0,
        "affection": previous.affection if previous else 0,
        "respect": previous.respect if previous else 0,
        "interaction_count": (
            previous.interaction_count if previous else 0
        ),
    }
    updated_values = {
        "trust": updated.trust,
        "affection": updated.affection,
        "respect": updated.respect,
        "interaction_count": updated.interaction_count,
    }
    changes = {
        field: {
            "before": previous_values[field],
            "after": updated_values[field],
        }
        for field in updated_values
        if previous_values[field] != updated_values[field]
    }

    await manager.broadcast(
        world_id=updated.world_id,
        tick=tick,
        event_type=StreamEventType.RELATIONSHIP_CHANGED,
        payload={
            "relationship_id": updated.relationship_id,
            "source_agent_id": updated.source_agent_id,
            "target_agent_id": updated.target_agent_id,
            "changes": changes,
        },
    )


async def publish_memory_created(
    memory: EpisodicMemory,
    *,
    manager: LiveStreamManager = stream_manager,
) -> None:
    await manager.broadcast(
        world_id=memory.world_id,
        tick=memory.creation_tick,
        event_type=StreamEventType.MEMORY_CREATED,
        payload={
            "memory_id": memory.memory_id,
            "owner_agent_id": memory.owner_agent_id,
            "content": memory.content,
            "importance": memory.importance,
            "emotional_value": memory.emotional_value,
            "source_event_sequence": memory.source_event_sequence,
            "source_agent_id": memory.source_agent_id,
            "embedding_model": memory.embedding_model,
        },
    )
