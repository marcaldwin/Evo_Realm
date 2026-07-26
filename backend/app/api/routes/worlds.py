from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status

from ...services.world_service import (
    InvalidWorldTransitionError,
    create_world,
    get_world,
    list_worlds,
    pause_world,
    resume_world,
    start_world,
    step_world,
)
from ...simulation.models import World
from ..schemas.world import (
    WorldCreate,
    WorldResponse,
    WorldSummaryResponse,
)


router = APIRouter(tags=["worlds"])


def _apply_lifecycle_transition(
    world_id: str,
    transition: Callable[[str], World | None],
) -> WorldResponse:
    try:
        world = transition(world_id)
    except InvalidWorldTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return WorldResponse.model_validate(world)


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


@router.post(
    "/api/worlds/{world_id}/start",
    response_model=WorldResponse,
    summary="Start a simulation world",
)
def start_simulation_world(world_id: str) -> WorldResponse:
    return _apply_lifecycle_transition(world_id, start_world)


@router.post(
    "/api/worlds/{world_id}/pause",
    response_model=WorldResponse,
    summary="Pause a simulation world",
)
def pause_simulation_world(world_id: str) -> WorldResponse:
    return _apply_lifecycle_transition(world_id, pause_world)


@router.post(
    "/api/worlds/{world_id}/resume",
    response_model=WorldResponse,
    summary="Resume a simulation world",
)
def resume_simulation_world(world_id: str) -> WorldResponse:
    return _apply_lifecycle_transition(world_id, resume_world)
