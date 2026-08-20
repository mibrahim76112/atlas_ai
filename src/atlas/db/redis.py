"""Redis client and dependency."""

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from atlas.core.config import get_settings

_settings = get_settings()

redis_client: aioredis.Redis = aioredis.from_url(
    str(_settings.redis_url),
    decode_responses=True,
)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency yielding the shared Redis client."""
    yield redis_client
