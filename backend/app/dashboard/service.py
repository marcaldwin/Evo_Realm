from ..db.session import SessionLocal
from .models import WorldDashboardMetrics
from .repository import DashboardMetricsRepository


def get_world_dashboard_metrics(
    world_id: str,
) -> WorldDashboardMetrics | None:
    with SessionLocal() as session:
        return DashboardMetricsRepository(session).get(world_id)
