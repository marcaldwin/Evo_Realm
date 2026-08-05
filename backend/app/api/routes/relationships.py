from fastapi import APIRouter, HTTPException, status

from ...services.relationship_service import list_world_relationships
from ...social.schemas import DirectionalRelationship


router = APIRouter(tags=["relationships"])


@router.get(
    "/api/worlds/{world_id}/relationships",
    response_model=list[DirectionalRelationship],
    summary="List relationships in a simulation world",
)
def list_simulation_world_relationships(
    world_id: str,
) -> list[DirectionalRelationship]:
    relationships = list_world_relationships(world_id)
    if relationships is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )
    return relationships
