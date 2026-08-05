from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.enums import (
    ConversationStatus,
    EventType,
    InteractionOutcome,
    ResourceType,
    WorldStatus,
)
from ..db.models import (
    AgentInventoryRecord,
    AgentRecord,
    ConversationOutcomeRecord,
    ConversationRecord,
    LocationInventoryRecord,
    LocationRecord,
    SimulationEventRecord,
    WorldRecord,
)
from .models import WorldDashboardMetrics


class DashboardMetricsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, world_id: str) -> WorldDashboardMetrics | None:
        location_food = (
            select(
                func.coalesce(
                    func.sum(LocationInventoryRecord.quantity),
                    0,
                )
            )
            .join(LocationRecord)
            .where(
                LocationRecord.world_database_id
                == WorldRecord.database_id,
                LocationInventoryRecord.resource_type
                == ResourceType.FOOD.value,
            )
            .correlate(WorldRecord)
            .scalar_subquery()
        )
        agent_food = (
            select(
                func.coalesce(
                    func.sum(AgentInventoryRecord.quantity),
                    0,
                )
            )
            .join(AgentRecord)
            .where(
                AgentRecord.world_database_id
                == WorldRecord.database_id,
                AgentInventoryRecord.resource_type
                == ResourceType.FOOD.value,
            )
            .correlate(WorldRecord)
            .scalar_subquery()
        )
        average_health = (
            select(func.coalesce(func.avg(AgentRecord.health), 0.0))
            .where(
                AgentRecord.world_database_id
                == WorldRecord.database_id
            )
            .correlate(WorldRecord)
            .scalar_subquery()
        )
        rejected_event_types = [
            event_type.value
            for event_type in EventType
            if event_type.value.endswith("_rejected")
        ]
        rejected_actions = (
            select(func.count(SimulationEventRecord.database_id))
            .where(
                SimulationEventRecord.world_database_id
                == WorldRecord.database_id,
                SimulationEventRecord.event_type.in_(
                    rejected_event_types
                ),
            )
            .correlate(WorldRecord)
            .scalar_subquery()
        )
        successful_trades = self._outcome_count(
            InteractionOutcome.SUCCESSFUL_TRADE,
        )
        emergency_help_events = self._outcome_count(
            InteractionOutcome.EMERGENCY_HELP,
        )
        active_conversations = (
            select(func.count(ConversationRecord.database_id))
            .where(
                ConversationRecord.world_database_id
                == WorldRecord.database_id,
                ConversationRecord.status
                == ConversationStatus.ACTIVE.value,
            )
            .correlate(WorldRecord)
            .scalar_subquery()
        )
        statement = (
            select(
                WorldRecord.id.label("world_id"),
                WorldRecord.current_tick,
                WorldRecord.status,
                (location_food + agent_food).label("total_food"),
                average_health.label("average_health"),
                successful_trades.label("successful_trades"),
                emergency_help_events.label(
                    "emergency_help_events"
                ),
                rejected_actions.label("rejected_actions"),
                active_conversations.label(
                    "active_conversations"
                ),
            )
            .where(WorldRecord.id == world_id)
        )
        row = self.session.execute(statement).mappings().one_or_none()
        if row is None:
            return None

        return WorldDashboardMetrics(
            world_id=row["world_id"],
            current_tick=row["current_tick"],
            status=WorldStatus(row["status"]),
            total_food=int(row["total_food"]),
            average_health=round(float(row["average_health"]), 2),
            successful_trades=row["successful_trades"],
            emergency_help_events=row["emergency_help_events"],
            rejected_actions=row["rejected_actions"],
            active_conversations=row["active_conversations"],
        )

    @staticmethod
    def _outcome_count(
        outcome_type: InteractionOutcome,
    ):
        return (
            select(func.count(ConversationOutcomeRecord.database_id))
            .join(ConversationRecord)
            .where(
                ConversationRecord.world_database_id
                == WorldRecord.database_id,
                ConversationOutcomeRecord.outcome_type
                == outcome_type.value,
                ConversationOutcomeRecord.confirmed.is_(True),
            )
            .correlate(WorldRecord)
            .scalar_subquery()
        )
