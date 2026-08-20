"""Shared route dependencies."""

from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.core.config import Settings, get_settings
from atlas.core.exceptions import AuthenticationError
from atlas.core.tokens import decode_token
from atlas.db.redis import get_redis
from atlas.db.session import get_db
from atlas.models.user import User
from atlas.repositories.user import UserRepository
from atlas.services.denylist import TokenDenylist

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Resolve the authenticated user from a bearer access token."""
    if credentials is None:
        raise AuthenticationError

    claims = decode_token(credentials.credentials, "access", settings)

    if await TokenDenylist(redis).is_revoked(claims.jti):
        raise AuthenticationError

    try:
        user_id = UUID(claims.subject)
    except ValueError as exc:
        raise AuthenticationError from exc

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
