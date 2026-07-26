"""Schemas for creating and returning simulation worlds."""

from collections import Counter
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...core.enums import (
    AgentStatus,
    EventType,
    LocationType,
    Occupation,
    ResourceType,
    WorldStatus,
)


NonNegativeInteger = Annotated[int, Field(ge=0)]
BoundedStat = Annotated[int, Field(ge=0, le=100)]
RequiredName = Annotated[str, Field(min_length=1, max_length=100)]
RequiredIdentifier = Annotated[str, Field(min_length=1, max_length=100)]


class ApiSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
    )


class LocationCreate(ApiSchema):
    id: RequiredIdentifier
    name: RequiredName
    location_type: LocationType
    x: int
    y: int
    capacity: NonNegativeInteger
    inventory: dict[ResourceType, NonNegativeInteger] = Field(
        default_factory=dict
    )


class AgentCreate(ApiSchema):
    id: RequiredIdentifier
    name: RequiredName
    occupation: Occupation
    location_id: RequiredIdentifier
    status: AgentStatus = AgentStatus.IDLE
    hunger: BoundedStat
    energy: BoundedStat
    health: BoundedStat
    money: NonNegativeInteger
    inventory: dict[ResourceType, NonNegativeInteger] = Field(
        default_factory=dict
    )


class WorldCreate(ApiSchema):
    name: RequiredName
    seed: int
    starting_tick: NonNegativeInteger = 0
    locations: list[LocationCreate] = Field(min_length=1)
    agents: list[AgentCreate]

    @model_validator(mode="after")
    def validate_world_relationships(self) -> Self:
        location_ids = [location.id for location in self.locations]
        if len(set(location_ids)) != len(location_ids):
            raise ValueError("Location IDs must be unique.")

        agent_ids = [agent.id for agent in self.agents]
        if len(set(agent_ids)) != len(agent_ids):
            raise ValueError("Agent IDs must be unique.")

        locations_by_id = {
            location.id: location
            for location in self.locations
        }
        occupancy = Counter(agent.location_id for agent in self.agents)

        for agent in self.agents:
            if agent.location_id not in locations_by_id:
                raise ValueError(
                    f"Agent {agent.id} references an unknown location."
                )

        for location in self.locations:
            if occupancy[location.id] > location.capacity:
                raise ValueError(
                    f"Location {location.id} capacity would be exceeded."
                )

        return self


class LocationResponse(ApiSchema):
    id: str
    name: str
    location_type: LocationType
    x: int
    y: int
    capacity: int
    inventory: dict[ResourceType, int]


class AgentResponse(ApiSchema):
    id: str
    name: str
    occupation: Occupation
    location_id: str
    status: AgentStatus
    hunger: int
    energy: int
    health: int
    money: int
    inventory: dict[ResourceType, int]


class SimulationEventResponse(ApiSchema):
    tick: int
    event_type: EventType
    agent_id: str
    location_id: str
    summary: str


class WorldSummaryResponse(ApiSchema):
    id: str
    name: str
    current_tick: int
    seed: int
    status: WorldStatus
    agent_count: int


class WorldResponse(ApiSchema):
    id: str
    name: str
    current_tick: int
    seed: int
    status: WorldStatus
    locations: list[LocationResponse]
    agents: list[AgentResponse]
    events: list[SimulationEventResponse]
