from fastapi import APIRouter, HTTPException, status

from ...dashboard.service import get_world_dashboard_metrics
from ..schemas.dashboard import WorldDashboardMetricsResponse


router = APIRouter(tags=["metrics"])


@router.get(
    "/api/worlds/{world_id}/metrics",
    response_model=WorldDashboardMetricsResponse,
    summary="Get dashboard metrics for a simulation world",
)
def get_simulation_world_metrics(
    world_id: str,
) -> WorldDashboardMetricsResponse:
    metrics = get_world_dashboard_metrics(world_id)
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return WorldDashboardMetricsResponse.model_validate(metrics)
