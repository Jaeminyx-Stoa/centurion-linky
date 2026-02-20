"""Simple Redis cache utility for application-level caching."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url, decode_responses=True
        )
    return _redis_client


async def cache_get(key: str) -> Any | None:
    """Get a cached value by key. Returns None on miss or error."""
    try:
        r = await _get_redis()
        data = await r.get(key)
        if data is not None:
            return json.loads(data)
    except Exception:
        logger.debug("Cache get failed for key=%s", key)
    return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Set a cached value with TTL. Fails silently."""
    try:
        r = await _get_redis()
        await r.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:
        logger.debug("Cache set failed for key=%s", key)


async def cache_delete(pattern: str) -> None:
    """Delete cached keys matching pattern. Fails silently."""
    try:
        r = await _get_redis()
        keys = []
        async for key in r.scan_iter(match=pattern, count=100):
            keys.append(key)
        if keys:
            await r.delete(*keys)
    except Exception:
        logger.debug("Cache delete failed for pattern=%s", pattern)
