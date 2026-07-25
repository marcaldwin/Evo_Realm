"""FastAPI application entry point."""

from fastapi import FastAPI

from .api.router import api_router


app = FastAPI(
    title="EvoRealm API",
    description="Backend API for the EvoRealm simulation",
    version="0.1.0",
)
app.include_router(api_router)
