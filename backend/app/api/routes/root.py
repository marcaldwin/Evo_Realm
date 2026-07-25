"""Root API route."""

from fastapi import APIRouter


router = APIRouter()


@router.get("/", summary="Get API information")
def get_api_information() -> dict[str, str]:
    return {
        "name": "EvoRealm API",
        "version": "0.1.0",
        "docs": "/docs",
    }
