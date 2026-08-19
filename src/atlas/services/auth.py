"""Account and authentication logic."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.core.exceptions import EmailAlreadyRegisteredError
from atlas.core.security import hash_password
from atlas.models.user import User
from atlas.repositories.user import UserRepository
from atlas.schemas.user import UserCreate


class AuthService:
    """Application logic for user accounts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

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
