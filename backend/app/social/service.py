from dataclasses import dataclass

from ..core.enums import (
    AgentStatus,
    ConversationStatus,
    DialogueAct,
    InteractionOutcome,
)
from ..db.models import ConversationRecord, RelationshipRecord
from .repository import SocialAgentData, SocialRepository
from .schemas import (
    ConversationOutcome,
    ConversationSession,
    ConversationTurn,
    DirectionalRelationship,
    OutcomeDetails,
)


MAX_CONVERSATION_DISTANCE = 1
MAX_CONVERSATION_TURNS = 4
AVAILABLE_STATUSES = {AgentStatus.IDLE}


class SocialServiceError(Exception):
    pass


class ConversationNotAllowedError(SocialServiceError):
    pass


class ConversationStateError(SocialServiceError):
    pass


@dataclass(frozen=True)
class RelationshipDelta:
    trust: int = 0
    affection: int = 0
    respect: int = 0
    interaction_count: int = 1


@dataclass(frozen=True)
class ConfirmedOutcomeResult:
    outcome: ConversationOutcome
    actor_relationship: DirectionalRelationship
    target_relationship: DirectionalRelationship


class ConversationService:
    def __init__(self, repository: SocialRepository) -> None:
        self.repository = repository

    def start(
        self,
        *,
        world_id: str,
        initiator_agent_id: str,
        participant_agent_id: str,
        start_tick: int,
    ) -> ConversationSession:
        if initiator_agent_id == participant_agent_id:
            raise ConversationNotAllowedError(
                "An agent cannot converse with itself."
            )
        if start_tick < 0:
            raise ValueError("Conversation start tick cannot be negative.")

        initiator = self._require_agent(
            world_id,
            initiator_agent_id,
        )
        participant = self._require_agent(
            world_id,
            participant_agent_id,
        )
        self._validate_agents_can_converse(initiator, participant)

        if self.repository.has_active_conversation(
            initiator.record.world_database_id,
            {
                initiator.record.database_id,
                participant.record.database_id,
            },
        ):
            raise ConversationNotAllowedError(
                "One or both agents are already in an active conversation."
            )

        return self.repository.add_conversation(
            initiator=initiator,
            participant=participant,
            start_tick=start_tick,
        )

    def add_turn(
        self,
        *,
        conversation_id: str,
        speaker_agent_id: str,
        dialogue_act: DialogueAct,
        message: str,
        creation_tick: int,
    ) -> ConversationSession:
        conversation = self._require_conversation_record(
            conversation_id,
            for_update=True,
        )
        if conversation.status != ConversationStatus.ACTIVE.value:
            raise ConversationStateError(
                "Cannot add a turn to a completed conversation."
            )
        if len(conversation.turns) >= MAX_CONVERSATION_TURNS:
            raise ConversationStateError(
                "Conversation has reached the four-turn limit."
            )

        initiator = self._require_agent(
            conversation.world.id,
            conversation.initiator_agent.id,
        )
        participant = self._require_agent(
            conversation.world.id,
            conversation.participant_agent.id,
        )
        self._validate_agents_can_converse(initiator, participant)

        turn_number = len(conversation.turns) + 1
        expected_speaker = (
            initiator
            if turn_number % 2 == 1
            else participant
        )
        listener = (
            participant
            if expected_speaker is initiator
            else initiator
        )
        if speaker_agent_id != expected_speaker.record.id:
            raise ConversationStateError(
                "Conversation turns must alternate speakers."
            )

        previous_tick = (
            conversation.turns[-1].creation_tick
            if conversation.turns
            else conversation.start_tick
        )
        if creation_tick < previous_tick:
            raise ConversationStateError(
                "Conversation turn tick cannot move backward."
            )

        validated_turn = ConversationTurn(
            turn_id="pending",
            conversation_id=conversation.id,
            turn_number=turn_number,
            speaker_agent_id=expected_speaker.record.id,
            listener_agent_id=listener.record.id,
            dialogue_act=dialogue_act,
            message=message,
            creation_tick=creation_tick,
        )
        return self.repository.add_turn(
            conversation=conversation,
            speaker=expected_speaker.record,
            listener=listener.record,
            dialogue_act=validated_turn.dialogue_act,
            message=validated_turn.message,
            creation_tick=validated_turn.creation_tick,
        )

    def complete(
        self,
        conversation_id: str,
        *,
        end_tick: int,
    ) -> ConversationSession:
        conversation = self._require_conversation_record(
            conversation_id,
            for_update=True,
        )
        if conversation.status == ConversationStatus.COMPLETED.value:
            raise ConversationStateError(
                "Conversation is already completed."
            )
        latest_tick = (
            conversation.turns[-1].creation_tick
            if conversation.turns
            else conversation.start_tick
        )
        if end_tick < latest_tick:
            raise ConversationStateError(
                "Conversation cannot end before its latest turn."
            )
        return self.repository.complete_conversation(
            conversation,
            end_tick,
        )

    def record_outcome(
        self,
        *,
        conversation_id: str,
        outcome_type: InteractionOutcome,
        actor_agent_id: str,
        target_agent_id: str,
        confirmation_tick: int,
        details: OutcomeDetails | None = None,
    ) -> ConversationOutcome:
        conversation = self._require_conversation_record(
            conversation_id,
            for_update=True,
        )
        participants = {
            conversation.initiator_agent.id:
                conversation.initiator_agent,
            conversation.participant_agent.id:
                conversation.participant_agent,
        }
        if actor_agent_id == target_agent_id:
            raise ConversationStateError(
                "A social outcome requires two different agents."
            )
        if {
            actor_agent_id,
            target_agent_id,
        } != set(participants):
            raise ConversationStateError(
                "Outcome agents must be conversation participants."
            )
        if confirmation_tick < conversation.start_tick:
            raise ConversationStateError(
                "Outcome cannot predate its conversation."
            )

        return self.repository.add_outcome(
            conversation=conversation,
            outcome_type=outcome_type,
            actor=participants[actor_agent_id],
            target=participants[target_agent_id],
            confirmation_tick=confirmation_tick,
            details=details or {},
        )

    def get(self, conversation_id: str) -> ConversationSession:
        conversation = self.repository.get_conversation(conversation_id)
        if conversation is None:
            raise LookupError("Conversation does not exist.")
        return conversation

    def _require_conversation_record(
        self,
        conversation_id: str,
        *,
        for_update: bool,
    ) -> ConversationRecord:
        conversation = self.repository.get_conversation_record(
            conversation_id,
            for_update=for_update,
        )
        if conversation is None:
            raise LookupError("Conversation does not exist.")
        return conversation

    def _require_agent(
        self,
        world_id: str,
        agent_id: str,
    ) -> SocialAgentData:
        agent = self.repository.get_agent(world_id, agent_id)
        if agent is None:
            raise LookupError("World or agent does not exist.")
        return agent

    @staticmethod
    def _validate_agents_can_converse(
        first: SocialAgentData,
        second: SocialAgentData,
    ) -> None:
        first_status = AgentStatus(first.record.status)
        second_status = AgentStatus(second.record.status)
        if (
            first_status not in AVAILABLE_STATUSES
            or second_status not in AVAILABLE_STATUSES
        ):
            raise ConversationNotAllowedError(
                "Both agents must be available to converse."
            )

        distance = abs(first.x - second.x) + abs(first.y - second.y)
        if distance > MAX_CONVERSATION_DISTANCE:
            raise ConversationNotAllowedError(
                "Agents are too far apart to converse."
            )


class RelationshipService:
    def __init__(self, repository: SocialRepository) -> None:
        self.repository = repository

    def confirm_outcome(
        self,
        outcome_id: str,
        *,
        confirmation_tick: int,
    ) -> ConfirmedOutcomeResult:
        outcome = self.repository.get_outcome_record(
            outcome_id,
            for_update=True,
        )
        if outcome is None:
            raise LookupError("Conversation outcome does not exist.")
        if confirmation_tick < outcome.conversation.start_tick:
            raise ConversationStateError(
                "Outcome cannot predate its conversation."
            )

        conversation = outcome.conversation
        agents_by_database_id = {
            conversation.initiator_agent.database_id:
                conversation.initiator_agent,
            conversation.participant_agent.database_id:
                conversation.participant_agent,
        }
        actor = agents_by_database_id[outcome.actor_agent_database_id]
        target = agents_by_database_id[outcome.target_agent_database_id]

        actor_relationship = self.repository.get_or_create_relationship(
            world_database_id=conversation.world_database_id,
            source_agent=actor,
            target_agent=target,
        )
        target_relationship = self.repository.get_or_create_relationship(
            world_database_id=conversation.world_database_id,
            source_agent=target,
            target_agent=actor,
        )

        if not outcome.relationship_applied:
            actor_delta, target_delta = self._deltas_for(
                InteractionOutcome(outcome.outcome_type)
            )
            self._apply_delta(actor_relationship, actor_delta)
            self._apply_delta(target_relationship, target_delta)
            outcome.confirmed = True
            outcome.confirmation_tick = confirmation_tick
            outcome.relationship_applied = True
            self.repository.session.flush()

        return ConfirmedOutcomeResult(
            outcome=self.repository.to_outcome(outcome),
            actor_relationship=self.repository.to_relationship(
                actor_relationship
            ),
            target_relationship=self.repository.to_relationship(
                target_relationship
            ),
        )

    def list_for_agent(
        self,
        world_id: str,
        source_agent_id: str,
    ) -> list[DirectionalRelationship]:
        return self.repository.list_relationships(
            world_id,
            source_agent_id,
        )

    @staticmethod
    def _apply_delta(
        record: RelationshipRecord,
        delta: RelationshipDelta,
    ) -> None:
        record.trust = max(-100, min(100, record.trust + delta.trust))
        record.affection = max(
            -100,
            min(100, record.affection + delta.affection),
        )
        record.respect = max(
            -100,
            min(100, record.respect + delta.respect),
        )
        record.interaction_count += delta.interaction_count

    @staticmethod
    def _deltas_for(
        outcome_type: InteractionOutcome,
    ) -> tuple[RelationshipDelta, RelationshipDelta]:
        if outcome_type == InteractionOutcome.SUCCESSFUL_TRADE:
            shared = RelationshipDelta(
                trust=5,
                affection=1,
                respect=3,
            )
            return shared, shared
        if outcome_type == InteractionOutcome.EMERGENCY_HELP:
            return (
                RelationshipDelta(affection=2, respect=2),
                RelationshipDelta(
                    trust=12,
                    affection=8,
                    respect=10,
                ),
            )
        if outcome_type == InteractionOutcome.REFUSAL:
            return (
                RelationshipDelta(),
                RelationshipDelta(
                    trust=-3,
                    affection=-2,
                    respect=-1,
                ),
            )
        if outcome_type == InteractionOutcome.PROMISE_FULFILLED:
            return (
                RelationshipDelta(),
                RelationshipDelta(
                    trust=10,
                    affection=4,
                    respect=7,
                ),
            )
        return (
            RelationshipDelta(),
            RelationshipDelta(
                trust=-15,
                affection=-6,
                respect=-10,
            ),
        )
