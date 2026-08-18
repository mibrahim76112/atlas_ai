"""Tests for the User model and the database fixtures themselves."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.models.user import User


async def test_user_can_be_persisted(db_session: AsyncSession) -> None:
    """A user round-trips through the database with server-side defaults applied."""
    db_session.add(User(email="adeel@example.com", password_hash="not-a-real-hash"))
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == "adeel@example.com")
    )
    saved = result.scalar_one()

    assert saved.id is not None
    assert saved.created_at is not None
    assert saved.updated_at is not None
    assert saved.is_active is True


async def test_email_must_be_unique(db_session: AsyncSession) -> None:
    """The unique constraint is enforced by Postgres, not by application code."""
    db_session.add(User(email="taken@example.com", password_hash="x"))
    await db_session.commit()

    db_session.add(User(email="taken@example.com", password_hash="y"))

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_isolation_a(db_session: AsyncSession) -> None:
    """Writes here must not survive into any other test."""
    db_session.add(User(email="dup@example.com", password_hash="x"))
    await db_session.commit()


async def test_isolation_b(db_session: AsyncSession) -> None:
    """Same email as test_isolation_a — passes only if rollback isolation works."""
    db_session.add(User(email="dup@example.com", password_hash="x"))
    await db_session.commit()