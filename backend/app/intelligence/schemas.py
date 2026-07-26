from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..core.enums import (
    ActionType,
    AgentStatus,
    Occupation,
    ResourceType,
)

RequiredIdentifier = Annotated[str, Field(min_length=1, max_length=100)]
RequiredDescription = Annotated[str, Field(min_length=1, max_length=300)]
PositiveQuantity = Annotated[int, Field(gt=0)]
BoundedStat = Annotated[int, Field(ge=0, le=100)]
NonNegativeInteger = Annotated[int, Field(ge=0)]
GoalPriority = Annotated[int, Field(ge=1, le=10)]
RelationshipScore = Annotated[int, Field(ge=-100, le=100)]
LatencyMilliseconds = Annotated[float, Field(ge=0)]
AttemptCount = Annotated[int, Field(ge=1, le=2)]

DecisionValidationResult = Literal[
    "valid",
    "valid_after_retry",
    "invalid_format",
    "impossible_action",
    "provider_error",
    "timeout",
]


class IntelligenceSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class TokenUsage(IntelligenceSchema):
    input_tokens: NonNegativeInteger = 0
    output_tokens: NonNegativeInteger = 0


class DecisionTelemetry(IntelligenceSchema):
    provider: RequiredIdentifier
    model: RequiredIdentifier
    prompt_version: RequiredIdentifier
    latency_ms: LatencyMilliseconds
    token_usage: TokenUsage
    validation_result: DecisionValidationResult
    attempt_count: AttemptCount
    fallback_used: bool


class AgentDecisionState(IntelligenceSchema):
    agent_id: RequiredIdentifier
    name: RequiredIdentifier
    occupation: Occupation
    status: AgentStatus
    location_id: RequiredIdentifier
    hunger: BoundedStat
    energy: BoundedStat
    health: BoundedStat
    money: NonNegativeInteger
    inventory: dict[ResourceType, NonNegativeInteger] = Field(
        default_factory=dict
    )


class GoalSummary(IntelligenceSchema):
    goal_id: RequiredIdentifier
    description: RequiredDescription
    priority: GoalPriority


class NearbyEntitySummary(IntelligenceSchema):
    entity_id: RequiredIdentifier
    entity_type: Literal["agent", "location"]
    name: RequiredIdentifier
    distance: NonNegativeInteger
    attributes: dict[str, str | int | bool] = Field(
        default_factory=dict
    )


class RelationshipSummary(IntelligenceSchema):
    other_agent_id: RequiredIdentifier
    relationship_type: RequiredIdentifier
    score: RelationshipScore


class AvailableAction(IntelligenceSchema):
    action_id: RequiredIdentifier
    action_type: ActionType
    description: RequiredDescription
    target_id: RequiredIdentifier | None = None
    resource_type: ResourceType | None = None
    quantity: PositiveQuantity | None = None


class DecisionContext(IntelligenceSchema):
    context_version: Literal["1.0"] = "1.0"
    world_id: RequiredIdentifier
    tick: NonNegativeInteger
    agent: AgentDecisionState
    goals: list[GoalSummary] = Field(default_factory=list)
    nearby_entities: list[NearbyEntitySummary] = Field(
        default_factory=list
    )
    relationships: list[RelationshipSummary] = Field(
        default_factory=list
    )
    available_actions: list[AvailableAction] = Field(min_length=1)
    fallback_action_id: RequiredIdentifier

    @model_validator(mode="after")
    def validate_actions(self) -> Self:
        action_ids = [
            action.action_id
            for action in self.available_actions
        ]

        if len(set(action_ids)) != len(action_ids):
            raise ValueError("Available action IDs must be unique.")

        if self.fallback_action_id not in action_ids:
            raise ValueError(
                "Fallback action must be available."
            )

        return self


class ActionProposalV1(IntelligenceSchema):
    schema_version: Literal["1.0"] = "1.0"
    action_id: RequiredIdentifier
    rationale: RequiredDescription


class DecisionResult(IntelligenceSchema):
    selected_action: AvailableAction
    proposal: ActionProposalV1 | None = None
    telemetry: DecisionTelemetry


