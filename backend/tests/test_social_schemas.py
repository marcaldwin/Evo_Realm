import pytest
from pydantic import ValidationError

from backend.app.core.enums import (
    ConversationStatus,
    DialogueAct,
)
from backend.app.social.schemas import (
    ConversationSession,
    ConversationTurn,
)


def make_turn(turn_number: int) -> ConversationTurn:
    if turn_number % 2 == 1:
        speaker = "elena"
        listener = "marco"
    else:
        speaker = "marco"
        listener = "elena"

    return ConversationTurn(
        turn_id=f"turn-{turn_number}",
        conversation_id="conversation-1",
        turn_number=turn_number,
        speaker_agent_id=speaker,
        listener_agent_id=listener,
        dialogue_act=DialogueAct.INFORM,
        message=f"Message number {turn_number}.",
        creation_tick=turn_number,
    )


def test_conversation_accepts_exactly_four_turns() -> None:
    conversation = ConversationSession(
        conversation_id="conversation-1",
        world_id="world-1",
        initiator_agent_id="elena",
        participant_agent_id="marco",
        status=ConversationStatus.COMPLETED,
        start_tick=0,
        end_tick=4,
        turns=[
            make_turn(1),
            make_turn(2),
            make_turn(3),
            make_turn(4),
        ],
    )

    assert len(conversation.turns) == 4


def test_active_conversation_rejects_four_turns() -> None:
    with pytest.raises(
        ValidationError,
        match="four-turn conversation must be completed",
    ):
        ConversationSession(
            conversation_id="conversation-1",
            world_id="world-1",
            initiator_agent_id="elena",
            participant_agent_id="marco",
            status=ConversationStatus.ACTIVE,
            start_tick=0,
            turns=[
                make_turn(1),
                make_turn(2),
                make_turn(3),
                make_turn(4),
            ],
        )
