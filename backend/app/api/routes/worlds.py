"""World API routes."""

from fastapi import APIRouter, status

from ...services.world_service import create_world
from ..schemas.world import WorldCreate, WorldResponse


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
