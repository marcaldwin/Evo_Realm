from ..db.session import SessionLocal
from ..social.repository import SocialRepository
from ..social.schemas import DirectionalRelationship


def list_world_relationships(
    world_id: str,
) -> list[DirectionalRelationship] | None:
    with SessionLocal() as session:
        repository = SocialRepository(session)
        if not repository.world_exists(world_id):
            return None
        return repository.list_world_relationships(world_id)
