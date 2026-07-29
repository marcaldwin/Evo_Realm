"""Top-level API router."""

from fastapi import APIRouter

from .routes.agents import router as agents_router
from .routes.events import router as events_router
from .routes.health import router as health_router
from .routes.root import router as root_router
from .routes.worlds import router as worlds_router
from .routes.stream import router as stream_router


api_router = APIRouter()
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(worlds_router)
api_router.include_router(agents_router)
api_router.include_router(events_router)
api_router.include_router(stream_router)
