"""Authentication endpoints."""

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.api.deps import CurrentUser
from atlas.core.config import Settings, get_settings
from atlas.db.redis import get_redis
from atlas.db.session import get_db
from atlas.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from atlas.schemas.user import UserCreate, UserRead
from atlas.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    """Provide an AuthService bound to this request's resources."""
    return AuthService(session, redis, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, service: AuthServiceDep) -> UserRead:
    """Register a new user account."""
    user = await service.register(payload)
    return UserRead.model_validate(user)


@router.post("/login")
async def login(payload: LoginRequest, service: AuthServiceDep) -> TokenPair:
    """Exchange email and password for a token pair."""
    return await service.login(payload)


@router.post("/refresh")
async def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenPair:
    """Rotate a refresh token, invalidating the one presented."""
    return await service.refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, service: AuthServiceDep) -> None:
    """Revoke a refresh token."""
    await service.logout(payload.refresh_token)


@router.get("/me")
async def me(user: CurrentUser) -> UserRead:
    """Return the authenticated user."""
    return UserRead.model_validate(user)
