import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level async Redis client
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        raise RuntimeError("Redis not connected.")
    return _redis


async def connect_redis():
    global _redis
    _redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,      # auto-decode bytes → str
        max_connections=20,
    )
    # Ping to validate connection at startup
    await _redis.ping()
    logger.info("Redis connected.")


async def disconnect_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        logger.info("Redis disconnected.")


# ── Cache helpers ─────────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl_seconds: int = 300):
    """Store JSON-serializable value with TTL. Default 5 minutes."""
    r = await get_redis()
    await r.setex(key, ttl_seconds, json.dumps(value, default=str))


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)


# ── Pub/Sub helpers (for WebSocket real-time notifications) ───────────────────

async def publish_to_channel(channel: str, message: dict):
    """Publish a message to a Redis channel (for WebSocket broadcasts)."""
    r = await get_redis()
    await r.publish(channel, json.dumps(message, default=str))


async def get_pubsub():
    """Returns a Redis pubsub object for WebSocket subscription."""
    r = await get_redis()
    return r.pubsub()