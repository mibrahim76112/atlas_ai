"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.db.session import get_db
from atlas.schemas.user import UserCreate, UserRead
from atlas.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuthService:
    """Provide an AuthService bound to the request's session."""
    return AuthService(session)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    """Register a new user account."""
    user = await service.register(payload)
    return UserRead.model_validate(user)
