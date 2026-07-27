from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..core.enums import (
    ConversationStatus,
    DialogueAct,
    InteractionOutcome,
)

RequiredIdentifier = Annotated[str, Field(min_length=1, max_length=100)]
RelationshipValue = Annotated[int, Field(ge=-100, le=100)]
NonNegativeInteger = Annotated[int, Field(ge=0)]
MessageContent = Annotated[str, Field(min_length=1, max_length=1000)]
TurnNumber = Annotated[int, Field(ge=1, le=4)]
OutcomeDetails = dict[str, str | int | bool]


class SocialSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class DirectionalRelationship(SocialSchema):
    relationship_id: RequiredIdentifier
    world_id: RequiredIdentifier
    source_agent_id: RequiredIdentifier
    target_agent_id: RequiredIdentifier
    trust: RelationshipValue = 0
    affection: RelationshipValue = 0
    respect: RelationshipValue = 0
    interaction_count: NonNegativeInteger = 0

    @model_validator(mode="after")
    def prevent_self_relationship(self) -> Self:
        if self.source_agent_id == self.target_agent_id:
            raise ValueError(
                "An agent cannot have a relationship with itself."
            )
        return self


class ConversationTurn(SocialSchema):
    turn_id: RequiredIdentifier
    conversation_id: RequiredIdentifier
    turn_number: TurnNumber
    speaker_agent_id: RequiredIdentifier
    listener_agent_id: RequiredIdentifier
    dialogue_act: DialogueAct
    message: MessageContent
    creation_tick: NonNegativeInteger

    @model_validator(mode="after")
    def prevent_self_message(self) -> Self:
        if self.speaker_agent_id == self.listener_agent_id:
            raise ValueError("An agent cannot message itself.")
        return self


class ConversationOutcome(SocialSchema):
    outcome_id: RequiredIdentifier
    conversation_id: RequiredIdentifier
    outcome_type: InteractionOutcome
    actor_agent_id: RequiredIdentifier
    target_agent_id: RequiredIdentifier
    confirmed: bool
    confirmation_tick: NonNegativeInteger
    details: OutcomeDetails = Field(default_factory=dict)
    relationship_applied: bool = False

    @model_validator(mode="after")
    def prevent_self_outcome(self) -> Self:
        if self.actor_agent_id == self.target_agent_id:
            raise ValueError(
                "A social outcome requires two different agents."
            )
        if self.relationship_applied and not self.confirmed:
            raise ValueError(
                "An unconfirmed outcome cannot update relationships."
            )
        return self


class ConversationSession(SocialSchema):
    conversation_id: RequiredIdentifier
    world_id: RequiredIdentifier
    initiator_agent_id: RequiredIdentifier
    participant_agent_id: RequiredIdentifier
    status: ConversationStatus
    start_tick: NonNegativeInteger
    end_tick: NonNegativeInteger | None = None
    turns: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=4,
    )
    outcomes: list[ConversationOutcome] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_conversation(self) -> Self:
        if self.initiator_agent_id == self.participant_agent_id:
            raise ValueError(
                "A conversation requires two different agents."
            )

        participants = {
            self.initiator_agent_id,
            self.participant_agent_id,
        }

        for expected_number, turn in enumerate(self.turns, start=1):
            if turn.conversation_id != self.conversation_id:
                raise ValueError(
                    "Every turn must belong to its conversation."
                )
            if turn.turn_number != expected_number:
                raise ValueError(
                    "Conversation turns must be sequential."
                )
            if {
                turn.speaker_agent_id,
                turn.listener_agent_id,
            } != participants:
                raise ValueError(
                    "Conversation turns must use its participants."
                )
            expected_speaker = (
                self.initiator_agent_id
                if expected_number % 2 == 1
                else self.participant_agent_id
            )
            if turn.speaker_agent_id != expected_speaker:
                raise ValueError(
                    "Conversation turns must alternate speakers."
                )
            if turn.creation_tick < self.start_tick:
                raise ValueError(
                    "Conversation turns cannot predate the conversation."
                )

        if any(
            later.creation_tick < earlier.creation_tick
            for earlier, later in zip(
                self.turns,
                self.turns[1:],
                strict=False,
            )
        ):
            raise ValueError(
                "Conversation turn ticks must be chronological."
            )

        for outcome in self.outcomes:
            if outcome.conversation_id != self.conversation_id:
                raise ValueError(
                    "Every outcome must belong to its conversation."
                )
            if {
                outcome.actor_agent_id,
                outcome.target_agent_id,
            } != participants:
                raise ValueError(
                    "Conversation outcomes must use its participants."
                )

        if (
            len(self.turns) == 4
            and self.status == ConversationStatus.ACTIVE
        ):
            raise ValueError(
                "A four-turn conversation must be completed."
            )

        if self.status == ConversationStatus.COMPLETED:
            if self.end_tick is None:
                raise ValueError(
                    "A completed conversation requires an end tick."
                )
        elif self.end_tick is not None:
            raise ValueError(
                "An active conversation cannot have an end tick."
            )

        if self.end_tick is not None and self.end_tick < self.start_tick:
            raise ValueError(
                "Conversation cannot end before it starts."
            )

        return self
