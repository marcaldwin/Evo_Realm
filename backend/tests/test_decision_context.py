import json

import pytest
from pydantic import ValidationError

from backend.app.core.enums import (
    ActionType,
    AgentStatus,
    LocationType,
    Occupation,
    ResourceType,
)
from backend.app.intelligence.context_builder import (
    build_decision_context,
)
from backend.app.intelligence.prompt import (
    build_decision_prompts,
    serialize_decision_context,
)
from backend.app.intelligence.schemas import (
    ActionProposalV1,
    AgentDecisionState,
    AvailableAction,
    DecisionContext,
    GoalSummary,
    RelationshipSummary,
)
from backend.app.simulation.models import Agent, Location, World


def make_world() -> tuple[World, Agent]:
    farmer = Agent(
        id="agent-1",
        name="Elena",
        occupation=Occupation.FARMER,
        location_id="farm-1",
        status=AgentStatus.IDLE,
        hunger=45,
        energy=80,
        health=95,
        money=8,
        inventory={ResourceType.FOOD: 2},
    )
    merchant = Agent(
        id="agent-2",
        name="Marco",
        occupation=Occupation.MERCHANT,
        location_id="market-1",
        status=AgentStatus.WORKING,
        hunger=30,
        energy=70,
        health=100,
        money=20,
    )
    world = World(
        id="world-1",
        name="Decision World",
        current_tick=15,
        seed=42,
        locations=[
            Location(
                id="farm-1",
                name="North Farm",
                location_type=LocationType.FARM,
                x=0,
                y=0,
                capacity=3,
                inventory={ResourceType.FOOD: 10},
            ),
            Location(
                id="market-1",
                name="Central Market",
                location_type=LocationType.MARKET,
                x=2,
                y=1,
                capacity=5,
            ),
        ],
        agents=[farmer, merchant],
    )
    return world, farmer


def make_actions() -> list[AvailableAction]:
    return [
        AvailableAction(
            action_id="rest",
            action_type=ActionType.REST,
            description="Rest at the farm.",
        ),
        AvailableAction(
            action_id="work",
            action_type=ActionType.WORK,
            description="Produce food at the farm.",
            target_id="farm-1",
        ),
    ]


def test_context_builder_creates_compact_deterministic_context() -> None:
    world, farmer = make_world()

    context = build_decision_context(
        world,
        farmer,
        available_actions=make_actions(),
        fallback_action_id="rest",
        goals=[
            GoalSummary(
                goal_id="goal-1",
                description="Maintain the town food supply.",
                priority=8,
            )
        ],
        relationships=[
            RelationshipSummary(
                other_agent_id="agent-2",
                relationship_type="trusted",
                score=25,
            )
        ],
    )

    assert context.context_version == "1.0"
    assert context.world_id == "world-1"
    assert context.tick == 15
    assert context.agent.agent_id == "agent-1"
    assert context.agent.inventory == {ResourceType.FOOD: 2}
    assert context.goals[0].goal_id == "goal-1"
    assert context.relationships[0].other_agent_id == "agent-2"
    assert [
        (entity.entity_type, entity.entity_id, entity.distance)
        for entity in context.nearby_entities
    ] == [
        ("location", "farm-1", 0),
        ("agent", "agent-2", 3),
        ("location", "market-1", 3),
    ]
    assert context.nearby_entities[0].attributes[
        "food_quantity"
    ] == 10

    farmer.inventory[ResourceType.FOOD] = 0

    assert context.agent.inventory == {ResourceType.FOOD: 2}


def test_serialized_context_is_compact_and_hides_fallback_policy() -> None:
    world, farmer = make_world()
    context = build_decision_context(
        world,
        farmer,
        available_actions=make_actions(),
        fallback_action_id="rest",
    )

    first_serialization = serialize_decision_context(context)
    second_serialization = serialize_decision_context(context)
    payload = json.loads(first_serialization)
    system_prompt, user_prompt = build_decision_prompts(context)

    assert first_serialization == second_serialization
    assert "fallback_action_id" not in payload
    assert "\n" not in first_serialization
    assert system_prompt
    assert first_serialization in user_prompt


def test_decision_context_rejects_duplicate_action_ids() -> None:
    action = make_actions()[0]

    with pytest.raises(
        ValidationError,
        match="Available action IDs must be unique",
    ):
        DecisionContext(
            world_id="world-1",
            tick=0,
            agent=AgentDecisionState(
                agent_id="agent-1",
                name="Elena",
                occupation=Occupation.FARMER,
                status=AgentStatus.IDLE,
                location_id="farm-1",
                hunger=0,
                energy=100,
                health=100,
                money=0,
            ),
            available_actions=[action, action],
            fallback_action_id="rest",
        )


def test_decision_context_requires_available_fallback() -> None:
    with pytest.raises(
        ValidationError,
        match="Fallback action must be available",
    ):
        DecisionContext(
            world_id="world-1",
            tick=0,
            agent=AgentDecisionState(
                agent_id="agent-1",
                name="Elena",
                occupation=Occupation.FARMER,
                status=AgentStatus.IDLE,
                location_id="farm-1",
                hunger=0,
                energy=100,
                health=100,
                money=0,
            ),
            available_actions=make_actions(),
            fallback_action_id="unknown",
        )


def test_action_proposal_requires_supported_schema_version() -> None:
    with pytest.raises(ValidationError):
        ActionProposalV1.model_validate(
            {
                "schema_version": "2.0",
                "action_id": "rest",
                "rationale": "Rest is the safest action.",
            }
        )
