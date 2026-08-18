"""Health check endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.core.config import Settings, get_settings
from atlas.db.session import get_db
import logging

from sqlalchemy import text
router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

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


class ReadinessResponse(BaseModel):
    """Readiness response payload."""

    status: str


@router.get("/health/ready")
async def readiness(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReadinessResponse:
    """Readiness probe: can we actually serve traffic?"""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc

    return ReadinessResponse(status="ready")