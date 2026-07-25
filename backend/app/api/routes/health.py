"""Health-check API routes."""

from fastapi import APIRouter, HTTPException, status

from ...db.health import is_database_ready

router = APIRouter()


@router.get("/health/live", summary="Check application liveness")
def check_liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready", summary="Check application readiness")
def check_readiness() -> dict[str, str]:
    if not is_database_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    return {"status": "ready"}
