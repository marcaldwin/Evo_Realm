from dataclasses import dataclass, field

from ..core.enums import AgentStatus, LocationType, Occupation, ResourceType


@dataclass
class Location:
    id: str
    name: str
    location_type: LocationType
    x: int
    y: int
    capacity: int


@dataclass
class Agent:
    id: str
    name: str
    occupation: Occupation
    location_id: str
    status: AgentStatus
    hunger: int
    energy: int
    health: int
    money: int
    inventory: dict[ResourceType, int] = field(default_factory=dict)


@dataclass
class World:
    id: str
    name: str
    current_tick: int
    seed: int
    locations: list[Location]
    agents: list[Agent]
