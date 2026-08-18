"""Shared test fixtures."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from atlas.core.config import get_settings
from atlas.db.base import Base
from atlas.db.session import get_db
from atlas.main import create_app

_base_url = make_url(str(get_settings().database_url))
TEST_DATABASE_URL = _base_url.set(database=f"{_base_url.database}_test")

if not TEST_DATABASE_URL.database or not TEST_DATABASE_URL.database.endswith("_test"):
    raise RuntimeError(f"Refusing to run tests against {TEST_DATABASE_URL.database!r}")

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def _create_schema() -> AsyncGenerator[None, None]:
    """Build the schema once for the whole test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A session wrapped in a transaction that is always rolled back."""
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """An HTTP client whose requests share the test's transaction."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
