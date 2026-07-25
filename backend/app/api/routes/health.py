"""Health-check API routes."""

from fastapi import APIRouter


router = APIRouter()


@router.get("/health/live", summary="Check application liveness")
def check_liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready", summary="Check application readiness")
def check_readiness() -> dict[str, str]:
    return {"status": "ready"}
