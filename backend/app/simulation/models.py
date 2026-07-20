from dataclasses import dataclass

from ..core.enums import AgentStatus, LocationType, Occupation


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


@dataclass
class World:
    id: str
    name: str
    current_tick: int
    seed: int
    locations: list[Location]
    agents: list[Agent]
