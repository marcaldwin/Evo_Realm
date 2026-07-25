"""Agent API routes."""

from fastapi import APIRouter, HTTPException, status

from ...services.world_service import list_world_agents
from ..schemas.agent import AgentSummaryResponse


router = APIRouter(tags=["agents"])


@router.get(
    "/api/worlds/{world_id}/agents",
    response_model=list[AgentSummaryResponse],
    summary="List agents in a simulation world",
)
def list_simulation_world_agents(
    world_id: str,
) -> list[AgentSummaryResponse]:
    agents = list_world_agents(world_id)
    if agents is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return [
        AgentSummaryResponse.model_validate(agent)
        for agent in agents
    ]
