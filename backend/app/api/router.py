"""Top-level API router."""

from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.root import router as root_router
from .routes.worlds import router as worlds_router


api_router = APIRouter()
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(worlds_router)
