"""Schemas for agent API responses."""

from ...core.enums import (
    AgentStatus,
    EventType,
    Occupation,
    ResourceType,
)
from ...memory.schemas import RetrievedMemory
from .world import (
    ApiSchema,
    BoundedStat,
    NonNegativeInteger,
)


class AgentSummaryResponse(ApiSchema):
    id: str
    name: str
    occupation: Occupation
    status: AgentStatus
    location_id: str
    hunger: BoundedStat
    energy: BoundedStat
    health: BoundedStat
    money: NonNegativeInteger
    inventory: dict[ResourceType, NonNegativeInteger]


class AgentActionResponse(ApiSchema):
    tick: NonNegativeInteger
    event_type: EventType
    location_id: str
    summary: str


class AgentInspectorResponse(AgentSummaryResponse):
    personality_traits: dict[str, int]
    active_goal: str | None
    recent_actions: list[AgentActionResponse]
    selected_retrieved_memories: list[RetrievedMemory]
