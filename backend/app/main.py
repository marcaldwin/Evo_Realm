from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .api.router import api_router
from .simulation.runtime import simulation_runtime


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await simulation_runtime.restore_running_worlds()
    try:
        yield
    finally:
        await simulation_runtime.shutdown()


app = FastAPI(
    title="EvoRealm API",
    description="Backend API for the EvoRealm simulation",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)
