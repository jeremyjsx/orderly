import logging

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def connect_redis() -> None:
    """Initialize Redis connection."""
    global _redis_client

    try:
        if settings.REDIS_PASSWORD:
            _redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
            )
        else:
            _redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

        await _redis_client.ping()
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
        raise


async def disconnect_redis() -> None:
    """Close Redis connection gracefully."""
    global _redis_client

    try:
        if _redis_client:
            await _redis_client.aclose()
            logger.info("Disconnected from Redis")
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")

    _redis_client = None


def get_redis() -> Redis:
    """Get Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call connect_redis() first.")
    return _redis_client


async def is_redis_connected() -> bool:
    """Check if Redis connection is active."""
    if _redis_client is None:
        return False
    try:
        await _redis_client.ping()
        return True
    except Exception:
        return False
