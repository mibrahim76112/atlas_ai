"""Health check endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from atlas.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Liveness response payload."""

    status: str
    app_name: str
    environment: str
    version: str


@router.get("/health")
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Liveness probe: is the process up and serving?"""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment,
        version="0.1.0",
    )
