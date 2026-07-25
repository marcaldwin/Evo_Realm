"""World API routes."""

from fastapi import APIRouter, HTTPException, status

from ...services.world_service import (
    create_world,
    get_world,
    list_worlds,
    step_world,
)
from ..schemas.world import (
    WorldCreate,
    WorldResponse,
    WorldSummaryResponse,
)


router = APIRouter(tags=["worlds"])


@router.post(
    "/api/worlds",
    response_model=WorldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a simulation world",
)
def create_simulation_world(configuration: WorldCreate) -> WorldResponse:
    world = create_world(configuration)
    return WorldResponse.model_validate(world)


@router.get(
    "/api/worlds",
    response_model=list[WorldSummaryResponse],
    summary="List simulation worlds",
)
def list_simulation_worlds() -> list[WorldSummaryResponse]:
    return [
        WorldSummaryResponse.model_validate(world)
        for world in list_worlds()
    ]


@router.get(
    "/api/worlds/{world_id}",
    response_model=WorldResponse,
    summary="Get a simulation world",
)
def get_simulation_world(world_id: str) -> WorldResponse:
    world = get_world(world_id)
    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return WorldResponse.model_validate(world)


@router.post(
    "/api/worlds/{world_id}/step",
    response_model=WorldResponse,
    summary="Advance a simulation world by one tick",
)
def step_simulation_world(world_id: str) -> WorldResponse:
    world = step_world(world_id)
    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return WorldResponse.model_validate(world)
