"""Schemas for agent API responses."""

from ...core.enums import (
    AgentStatus,
    Occupation,
    ResourceType,
)
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
