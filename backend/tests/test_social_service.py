import pytest
from sqlalchemy.orm import sessionmaker

from backend.app.core.enums import (
    AgentStatus,
    ConversationStatus,
    DialogueAct,
    InteractionOutcome,
    LocationType,
    Occupation,
)
from backend.app.repositories.world_repository import WorldRepository
from backend.app.simulation.models import Agent, Location, World
from backend.app.social.repository import SocialRepository
from backend.app.social.service import (
    ConversationNotAllowedError,
    ConversationService,
    ConversationStateError,
    RelationshipService,
)


def make_social_world() -> World:
    return World(
        id="social-world",
        name="Social World",
        current_tick=10,
        seed=42,
        locations=[
            Location(
                id="center",
                name="Center",
                location_type=LocationType.TOWN_HALL,
                x=0,
                y=0,
                capacity=5,
            ),
            Location(
                id="nearby",
                name="Nearby",
                location_type=LocationType.MARKET,
                x=1,
                y=0,
                capacity=5,
            ),
            Location(
                id="far",
                name="Far",
                location_type=LocationType.FARM,
                x=5,
                y=0,
                capacity=5,
            ),
        ],
        agents=[
            Agent(
                id="elena",
                name="Elena",
                occupation=Occupation.FARMER,
                location_id="center",
                status=AgentStatus.IDLE,
                hunger=20,
                energy=90,
                health=100,
                money=10,
            ),
            Agent(
                id="marco",
                name="Marco",
                occupation=Occupation.MERCHANT,
                location_id="nearby",
                status=AgentStatus.IDLE,
                hunger=30,
                energy=80,
                health=100,
                money=20,
            ),
            Agent(
                id="sofia",
                name="Sofia",
                occupation=Occupation.DOCTOR,
                location_id="far",
                status=AgentStatus.IDLE,
                hunger=10,
                energy=100,
                health=100,
                money=15,
            ),
            Agent(
                id="liam",
                name="Liam",
                occupation=Occupation.WORKER,
                location_id="center",
                status=AgentStatus.WORKING,
                hunger=40,
                energy=60,
                health=100,
                money=5,
            ),
        ],
    )


def start_elena_marco_conversation(
    conversation_service: ConversationService,
) -> str:
    conversation = conversation_service.start(
        world_id="social-world",
        initiator_agent_id="elena",
        participant_agent_id="marco",
        start_tick=10,
    )
    return conversation.conversation_id


def test_four_turn_conversation_persists_messages_and_dialogue_acts(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_social_world())
        conversation_service = ConversationService(
            SocialRepository(session)
        )
        conversation_id = start_elena_marco_conversation(
            conversation_service
        )
        turns = [
            ("elena", DialogueAct.REQUEST, "Can you share food?"),
            ("marco", DialogueAct.OFFER, "I can offer one food."),
            ("elena", DialogueAct.AGREE, "I agree to that offer."),
            ("marco", DialogueAct.THANK, "Thank you for agreeing."),
        ]
        conversation = None
        for offset, (speaker, act, message) in enumerate(turns, start=1):
            conversation = conversation_service.add_turn(
                conversation_id=conversation_id,
                speaker_agent_id=speaker,
                dialogue_act=act,
                message=message,
                creation_tick=10 + offset,
            )

    assert conversation is not None
    assert conversation.status == ConversationStatus.COMPLETED
    assert conversation.end_tick == 14
    assert [turn.message for turn in conversation.turns] == [
        message for _, _, message in turns
    ]
    assert [turn.dialogue_act for turn in conversation.turns] == [
        act for _, act, _ in turns
    ]

    with test_session_factory() as session:
        restored = SocialRepository(session).get_conversation(
            conversation_id
        )

    assert restored == conversation


def test_conversation_rejects_agents_who_are_too_far_apart(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_social_world())
        service = ConversationService(SocialRepository(session))

        with pytest.raises(
            ConversationNotAllowedError,
            match="too far apart",
        ):
            service.start(
                world_id="social-world",
                initiator_agent_id="elena",
                participant_agent_id="sofia",
                start_tick=10,
            )


def test_conversation_rejects_unavailable_agents(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_social_world())
        service = ConversationService(SocialRepository(session))

        with pytest.raises(
            ConversationNotAllowedError,
            match="must be available",
        ):
            service.start(
                world_id="social-world",
                initiator_agent_id="elena",
                participant_agent_id="liam",
                start_tick=10,
            )


def test_agent_cannot_join_two_active_conversations(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        world = make_social_world()
        world.agents[2].location_id = "center"
        WorldRepository(session).add(world)
        service = ConversationService(SocialRepository(session))
        start_elena_marco_conversation(service)

        with pytest.raises(
            ConversationNotAllowedError,
            match="already in an active conversation",
        ):
            service.start(
                world_id="social-world",
                initiator_agent_id="elena",
                participant_agent_id="sofia",
                start_tick=10,
            )


def test_turns_must_alternate_speakers(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_social_world())
        service = ConversationService(SocialRepository(session))
        conversation_id = start_elena_marco_conversation(service)
        service.add_turn(
            conversation_id=conversation_id,
            speaker_agent_id="elena",
            dialogue_act=DialogueAct.INFORM,
            message="The market has food.",
            creation_tick=11,
        )

        with pytest.raises(
            ConversationStateError,
            match="must alternate speakers",
        ):
            service.add_turn(
                conversation_id=conversation_id,
                speaker_agent_id="elena",
                dialogue_act=DialogueAct.INFORM,
                message="I am speaking twice.",
                creation_tick=12,
            )


def test_natural_dialogue_does_not_change_relationships_or_world_state(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        world = make_social_world()
        WorldRepository(session).add(world)
        repository = SocialRepository(session)
        conversation_service = ConversationService(repository)
        relationship_service = RelationshipService(repository)
        conversation_id = start_elena_marco_conversation(
            conversation_service
        )
        conversation_service.add_turn(
            conversation_id=conversation_id,
            speaker_agent_id="elena",
            dialogue_act=DialogueAct.PROMISE,
            message="I promise to bring food.",
            creation_tick=11,
        )
        restored_world = WorldRepository(session).get("social-world")

        relationships = relationship_service.list_for_agent(
            "social-world",
            "elena",
        )

    assert relationships == []
    assert restored_world is not None
    assert restored_world.agents == world.agents


@pytest.mark.parametrize(
    (
        "outcome_type",
        "expected_actor",
        "expected_target",
    ),
    [
        (
            InteractionOutcome.SUCCESSFUL_TRADE,
            (5, 1, 3, 1),
            (5, 1, 3, 1),
        ),
        (
            InteractionOutcome.EMERGENCY_HELP,
            (0, 2, 2, 1),
            (12, 8, 10, 1),
        ),
        (
            InteractionOutcome.REFUSAL,
            (0, 0, 0, 1),
            (-3, -2, -1, 1),
        ),
        (
            InteractionOutcome.PROMISE_FULFILLED,
            (0, 0, 0, 1),
            (10, 4, 7, 1),
        ),
        (
            InteractionOutcome.BROKEN_PROMISE,
            (0, 0, 0, 1),
            (-15, -6, -10, 1),
        ),
    ],
)
def test_confirmed_outcomes_update_directional_relationships(
    database_world_store: None,
    test_session_factory: sessionmaker,
    outcome_type: InteractionOutcome,
    expected_actor: tuple[int, int, int, int],
    expected_target: tuple[int, int, int, int],
) -> None:
    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_social_world())
        repository = SocialRepository(session)
        conversation_service = ConversationService(repository)
        relationship_service = RelationshipService(repository)
        conversation_id = start_elena_marco_conversation(
            conversation_service
        )
        outcome = conversation_service.record_outcome(
            conversation_id=conversation_id,
            outcome_type=outcome_type,
            actor_agent_id="elena",
            target_agent_id="marco",
            confirmation_tick=11,
            details={"verified": True},
        )

        assert relationship_service.list_for_agent(
            "social-world",
            "elena",
        ) == []

        result = relationship_service.confirm_outcome(
            outcome.outcome_id,
            confirmation_tick=12,
        )

    actor = result.actor_relationship
    target = result.target_relationship
    assert (
        actor.trust,
        actor.affection,
        actor.respect,
        actor.interaction_count,
    ) == expected_actor
    assert (
        target.trust,
        target.affection,
        target.respect,
        target.interaction_count,
    ) == expected_target
    assert result.outcome.confirmed is True
    assert result.outcome.relationship_applied is True


def test_confirming_same_outcome_twice_is_idempotent_and_persistent(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_social_world())
        repository = SocialRepository(session)
        conversation_service = ConversationService(repository)
        relationship_service = RelationshipService(repository)
        conversation_id = start_elena_marco_conversation(
            conversation_service
        )
        outcome = conversation_service.record_outcome(
            conversation_id=conversation_id,
            outcome_type=InteractionOutcome.EMERGENCY_HELP,
            actor_agent_id="elena",
            target_agent_id="marco",
            confirmation_tick=11,
        )
        first = relationship_service.confirm_outcome(
            outcome.outcome_id,
            confirmation_tick=12,
        )
        second = relationship_service.confirm_outcome(
            outcome.outcome_id,
            confirmation_tick=13,
        )

    assert second.actor_relationship == first.actor_relationship
    assert second.target_relationship == first.target_relationship

    with test_session_factory() as session:
        repository = SocialRepository(session)
        elena_relationships = repository.list_relationships(
            "social-world",
            "elena",
        )
        marco_relationships = repository.list_relationships(
            "social-world",
            "marco",
        )

    assert elena_relationships == [first.actor_relationship]
    assert marco_relationships == [first.target_relationship]
