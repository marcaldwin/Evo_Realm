"""Simulation event API routes."""

from fastapi import APIRouter, HTTPException, status

from ...services.world_service import list_world_events
from ..schemas.world import SimulationEventResponse


router = APIRouter(tags=["events"])


@router.get(
    "/api/worlds/{world_id}/events",
    response_model=list[SimulationEventResponse],
    summary="List events for a simulation world",
)
def list_simulation_world_events(
    world_id: str,
) -> list[SimulationEventResponse]:
    events = list_world_events(world_id)
    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return [
        SimulationEventResponse.model_validate(event)
        for event in events
    ]
