from dataclasses import dataclass

from ..core.enums import WorldStatus


@dataclass(frozen=True)
class WorldDashboardMetrics:
    world_id: str
    current_tick: int
    status: WorldStatus
    total_food: int
    average_health: float
    successful_trades: int
    emergency_help_events: int
    rejected_actions: int
    active_conversations: int
