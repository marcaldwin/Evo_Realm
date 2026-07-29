"""Agent API routes."""

from fastapi import APIRouter, HTTPException, status

from ...services.world_service import (
    get_world_agent_inspector,
    list_world_agents,
)
from ..schemas.agent import (
    AgentActionResponse,
    AgentInspectorResponse,
    AgentSummaryResponse,
)


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


@router.get(
    "/api/worlds/{world_id}/agents/{agent_id}",
    response_model=AgentInspectorResponse,
    summary="Get a simulation agent",
)
def get_simulation_world_agent(
    world_id: str,
    agent_id: str,
) -> AgentInspectorResponse:
    inspector = get_world_agent_inspector(world_id, agent_id)
    if inspector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    agent = inspector.agent
    return AgentInspectorResponse(
        id=agent.id,
        name=agent.name,
        occupation=agent.occupation,
        status=agent.status,
        location_id=agent.location_id,
        hunger=agent.hunger,
        energy=agent.energy,
        health=agent.health,
        money=agent.money,
        inventory=agent.inventory,
        personality_traits=agent.personality_traits,
        active_goal=agent.active_goal,
        recent_actions=[
            AgentActionResponse(
                tick=event.tick,
                event_type=event.event_type,
                location_id=event.location_id,
                summary=event.summary,
            )
            for event in inspector.recent_actions
        ],
        selected_retrieved_memories=(
            inspector.selected_retrieved_memories
        ),
    )
