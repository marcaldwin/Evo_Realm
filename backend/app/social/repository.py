from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..core.enums import (
    ConversationStatus,
    DialogueAct,
    InteractionOutcome,
)
from ..db.models import (
    AgentRecord,
    ConversationOutcomeRecord,
    ConversationRecord,
    ConversationTurnRecord,
    LocationRecord,
    RelationshipRecord,
    WorldRecord,
)
from .schemas import (
    ConversationOutcome,
    ConversationSession,
    ConversationTurn,
    DirectionalRelationship,
    OutcomeDetails,
)


@dataclass(frozen=True)
class SocialAgentData:
    record: AgentRecord
    world_id: str
    x: int
    y: int


class SocialRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_agent(
        self,
        world_id: str,
        agent_id: str,
    ) -> SocialAgentData | None:
        statement = (
            select(AgentRecord, WorldRecord.id, LocationRecord.x, LocationRecord.y)
            .join(
                WorldRecord,
                AgentRecord.world_database_id == WorldRecord.database_id,
            )
            .join(
                LocationRecord,
                AgentRecord.location_database_id
                == LocationRecord.database_id,
            )
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == agent_id,
            )
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        return SocialAgentData(
            record=row[0],
            world_id=row[1],
            x=row[2],
            y=row[3],
        )

    def has_active_conversation(
        self,
        world_database_id: int,
        agent_database_ids: set[int],
    ) -> bool:
        statement = (
            select(ConversationRecord.database_id)
            .where(
                ConversationRecord.world_database_id == world_database_id,
                ConversationRecord.status
                == ConversationStatus.ACTIVE.value,
                or_(
                    ConversationRecord.initiator_agent_database_id.in_(
                        agent_database_ids
                    ),
                    ConversationRecord.participant_agent_database_id.in_(
                        agent_database_ids
                    ),
                ),
            )
            .limit(1)
        )
        return self.session.scalar(statement) is not None

    def add_conversation(
        self,
        *,
        initiator: SocialAgentData,
        participant: SocialAgentData,
        start_tick: int,
    ) -> ConversationSession:
        record = ConversationRecord(
            id=str(uuid4()),
            world_database_id=initiator.record.world_database_id,
            initiator_agent=initiator.record,
            participant_agent=participant.record,
            status=ConversationStatus.ACTIVE.value,
            start_tick=start_tick,
        )
        self.session.add(record)
        self.session.flush()
        return self._to_conversation(record, initiator.world_id)

    def get_conversation_record(
        self,
        conversation_id: str,
        *,
        for_update: bool = False,
    ) -> ConversationRecord | None:
        statement = (
            select(ConversationRecord)
            .where(ConversationRecord.id == conversation_id)
            .options(
                selectinload(ConversationRecord.world),
                selectinload(ConversationRecord.initiator_agent),
                selectinload(ConversationRecord.participant_agent),
                selectinload(ConversationRecord.turns),
                selectinload(ConversationRecord.outcomes),
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def get_conversation(
        self,
        conversation_id: str,
    ) -> ConversationSession | None:
        record = self.get_conversation_record(conversation_id)
        if record is None:
            return None
        return self._to_conversation(record, record.world.id)

    def add_turn(
        self,
        *,
        conversation: ConversationRecord,
        speaker: AgentRecord,
        listener: AgentRecord,
        dialogue_act: DialogueAct,
        message: str,
        creation_tick: int,
    ) -> ConversationSession:
        turn_number = len(conversation.turns) + 1
        conversation.turns.append(
            ConversationTurnRecord(
                id=str(uuid4()),
                turn_number=turn_number,
                speaker_agent_database_id=speaker.database_id,
                listener_agent_database_id=listener.database_id,
                dialogue_act=dialogue_act.value,
                message=message,
                creation_tick=creation_tick,
            )
        )
        if turn_number == 4:
            conversation.status = ConversationStatus.COMPLETED.value
            conversation.end_tick = creation_tick
        self.session.flush()
        return self._to_conversation(
            conversation,
            conversation.world.id,
        )

    def complete_conversation(
        self,
        conversation: ConversationRecord,
        end_tick: int,
    ) -> ConversationSession:
        conversation.status = ConversationStatus.COMPLETED.value
        conversation.end_tick = end_tick
        self.session.flush()
        return self._to_conversation(
            conversation,
            conversation.world.id,
        )

    def add_outcome(
        self,
        *,
        conversation: ConversationRecord,
        outcome_type: InteractionOutcome,
        actor: AgentRecord,
        target: AgentRecord,
        confirmation_tick: int,
        details: OutcomeDetails,
    ) -> ConversationOutcome:
        record = ConversationOutcomeRecord(
            id=str(uuid4()),
            outcome_type=outcome_type.value,
            actor_agent_database_id=actor.database_id,
            target_agent_database_id=target.database_id,
            confirmed=False,
            confirmation_tick=confirmation_tick,
            details=dict(details),
            relationship_applied=False,
        )
        conversation.outcomes.append(record)
        self.session.flush()
        return self._to_outcome(record, conversation)

    def get_outcome_record(
        self,
        outcome_id: str,
        *,
        for_update: bool = False,
    ) -> ConversationOutcomeRecord | None:
        statement = (
            select(ConversationOutcomeRecord)
            .where(ConversationOutcomeRecord.id == outcome_id)
            .options(
                selectinload(ConversationOutcomeRecord.conversation)
                .selectinload(ConversationRecord.world),
                selectinload(ConversationOutcomeRecord.conversation)
                .selectinload(ConversationRecord.initiator_agent),
                selectinload(ConversationOutcomeRecord.conversation)
                .selectinload(ConversationRecord.participant_agent),
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def get_or_create_relationship(
        self,
        *,
        world_database_id: int,
        source_agent: AgentRecord,
        target_agent: AgentRecord,
    ) -> RelationshipRecord:
        statement = (
            select(RelationshipRecord)
            .where(
                RelationshipRecord.source_agent_database_id
                == source_agent.database_id,
                RelationshipRecord.target_agent_database_id
                == target_agent.database_id,
            )
            .options(
                selectinload(RelationshipRecord.world),
                selectinload(RelationshipRecord.source_agent),
                selectinload(RelationshipRecord.target_agent),
            )
            .with_for_update()
        )
        record = self.session.scalar(statement)
        if record is not None:
            return record

        record = RelationshipRecord(
            id=str(uuid4()),
            world_database_id=world_database_id,
            source_agent=source_agent,
            target_agent=target_agent,
            trust=0,
            affection=0,
            respect=0,
            interaction_count=0,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_relationships(
        self,
        world_id: str,
        source_agent_id: str,
    ) -> list[DirectionalRelationship]:
        statement = (
            select(RelationshipRecord)
            .join(
                WorldRecord,
                RelationshipRecord.world_database_id
                == WorldRecord.database_id,
            )
            .join(
                AgentRecord,
                RelationshipRecord.source_agent_database_id
                == AgentRecord.database_id,
            )
            .where(
                WorldRecord.id == world_id,
                AgentRecord.id == source_agent_id,
            )
            .options(
                selectinload(RelationshipRecord.world),
                selectinload(RelationshipRecord.source_agent),
                selectinload(RelationshipRecord.target_agent),
            )
            .order_by(RelationshipRecord.target_agent_database_id)
        )
        return [
            self.to_relationship(record)
            for record in self.session.scalars(statement)
        ]

    def to_outcome(
        self,
        record: ConversationOutcomeRecord,
    ) -> ConversationOutcome:
        return self._to_outcome(record, record.conversation)

    @staticmethod
    def to_relationship(
        record: RelationshipRecord,
    ) -> DirectionalRelationship:
        return DirectionalRelationship(
            relationship_id=record.id,
            world_id=record.world.id,
            source_agent_id=record.source_agent.id,
            target_agent_id=record.target_agent.id,
            trust=record.trust,
            affection=record.affection,
            respect=record.respect,
            interaction_count=record.interaction_count,
        )

    @classmethod
    def _to_conversation(
        cls,
        record: ConversationRecord,
        world_id: str,
    ) -> ConversationSession:
        initiator = record.initiator_agent
        participant = record.participant_agent
        agents_by_database_id = {
            initiator.database_id: initiator.id,
            participant.database_id: participant.id,
        }
        return ConversationSession(
            conversation_id=record.id,
            world_id=world_id,
            initiator_agent_id=initiator.id,
            participant_agent_id=participant.id,
            status=ConversationStatus(record.status),
            start_tick=record.start_tick,
            end_tick=record.end_tick,
            turns=[
                ConversationTurn(
                    turn_id=turn.id,
                    conversation_id=record.id,
                    turn_number=turn.turn_number,
                    speaker_agent_id=agents_by_database_id[
                        turn.speaker_agent_database_id
                    ],
                    listener_agent_id=agents_by_database_id[
                        turn.listener_agent_database_id
                    ],
                    dialogue_act=DialogueAct(turn.dialogue_act),
                    message=turn.message,
                    creation_tick=turn.creation_tick,
                )
                for turn in record.turns
            ],
            outcomes=[
                cls._to_outcome(outcome, record)
                for outcome in record.outcomes
            ],
        )

    @staticmethod
    def _to_outcome(
        record: ConversationOutcomeRecord,
        conversation: ConversationRecord,
    ) -> ConversationOutcome:
        agents_by_database_id = {
            conversation.initiator_agent.database_id:
                conversation.initiator_agent.id,
            conversation.participant_agent.database_id:
                conversation.participant_agent.id,
        }
        return ConversationOutcome(
            outcome_id=record.id,
            conversation_id=conversation.id,
            outcome_type=InteractionOutcome(record.outcome_type),
            actor_agent_id=agents_by_database_id[
                record.actor_agent_database_id
            ],
            target_agent_id=agents_by_database_id[
                record.target_agent_database_id
            ],
            confirmed=record.confirmed,
            confirmation_tick=record.confirmation_tick,
            details=dict(record.details),
            relationship_applied=record.relationship_applied,
        )
