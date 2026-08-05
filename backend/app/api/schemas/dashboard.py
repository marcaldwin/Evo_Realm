from ...core.enums import WorldStatus
from .world import ApiSchema, NonNegativeInteger


class WorldDashboardMetricsResponse(ApiSchema):
    world_id: str
    current_tick: NonNegativeInteger
    status: WorldStatus
    total_food: NonNegativeInteger
    average_health: float
    successful_trades: NonNegativeInteger
    emergency_help_events: NonNegativeInteger
    rejected_actions: NonNegativeInteger
    active_conversations: NonNegativeInteger
