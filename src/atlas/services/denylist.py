"""Revoked-token tracking, backed by Redis."""

from datetime import UTC, datetime

import redis.asyncio as aioredis

_PREFIX = "denylist:jti:"


class TokenDenylist:
    """Marks token IDs as revoked until they would have expired anyway."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        ttl = int((expires_at - datetime.now(UTC)).total_seconds())
        if ttl > 0:
            await self._redis.set(f"{_PREFIX}{jti}", "1", ex=ttl)

    async def is_revoked(self, jti: str) -> bool:
        return bool(await self._redis.exists(f"{_PREFIX}{jti}"))
