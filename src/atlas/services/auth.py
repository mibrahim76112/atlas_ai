"""Account and authentication logic."""

from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.core.config import Settings
from atlas.core.exceptions import AuthenticationError, EmailAlreadyRegisteredError
from atlas.core.security import hash_password, needs_rehash, verify_password
from atlas.core.tokens import create_access_token, create_refresh_token, decode_token
from atlas.models.user import User
from atlas.repositories.user import UserRepository
from atlas.schemas.auth import LoginRequest, TokenPair
from atlas.schemas.user import UserCreate
from atlas.services.denylist import TokenDenylist


class AuthService:
    """Application logic for accounts and credentials."""

    def __init__(
        self,
        session: AsyncSession,
        redis: aioredis.Redis,
        settings: Settings,
    ) -> None:
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)
        self._denylist = TokenDenylist(redis)

    async def register(self, payload: UserCreate) -> User:
        """Create a user, or raise if the email is taken."""
        email = payload.email.strip().lower()

        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(email=email, password_hash=hash_password(payload.password))

        try:
            await self._users.add(user)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError from exc

        return user

    async def login(self, payload: LoginRequest) -> TokenPair:
        """Exchange credentials for a token pair."""
        email = payload.email.strip().lower()
        user = await self._users.get_by_email(email)

        if user is None:
            # Hash anyway so the response time doesn't reveal whether
            # the account exists.
            hash_password(payload.password)
            raise AuthenticationError

        if not verify_password(payload.password, user.password_hash):
            raise AuthenticationError

        if not user.is_active:
            raise AuthenticationError

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(payload.password)
            await self._session.commit()

        return self._issue_pair(str(user.id))

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Rotate a refresh token, invalidating the one presented."""
        claims = decode_token(refresh_token, "refresh", self._settings)

        if await self._denylist.is_revoked(claims.jti):
            raise AuthenticationError

        user = await self._get_active_user(claims.subject)

        await self._denylist.revoke(claims.jti, claims.expires_at)
        return self._issue_pair(str(user.id))

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token."""
        claims = decode_token(refresh_token, "refresh", self._settings)
        await self._denylist.revoke(claims.jti, claims.expires_at)

    async def _get_active_user(self, subject: str) -> User:
        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise AuthenticationError from exc

        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError
        return user

    def _issue_pair(self, subject: str) -> TokenPair:
        access = create_access_token(subject, self._settings)
        refresh = create_refresh_token(subject, self._settings)
        return TokenPair(
            access_token=access.token,
            refresh_token=refresh.token,
            expires_in=self._settings.access_token_expire_minutes * 60,
        )
