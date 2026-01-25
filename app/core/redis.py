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


REFRESH_TOKEN_PREFIX = "refresh_token"


def _get_refresh_token_key(user_id: str, jti: str) -> str:
    """Generate Redis key for a refresh token."""
    return f"{REFRESH_TOKEN_PREFIX}:{user_id}:{jti}"


def _get_user_tokens_pattern(user_id: str) -> str:
    """Generate pattern to match all refresh tokens for a user."""
    return f"{REFRESH_TOKEN_PREFIX}:{user_id}:*"


async def store_refresh_token(user_id: str, jti: str, ttl_days: int = 7) -> bool:
    """
    Store a refresh token in Redis.

    Args:
        user_id: The user's ID
        jti: The token's unique identifier
        ttl_days: Time to live in days

    Returns:
        True if stored successfully
    """
    if _redis_client is None:
        logger.warning("Redis not connected, cannot store refresh token")
        return False

    try:
        key = _get_refresh_token_key(user_id, jti)
        ttl_seconds = ttl_days * 24 * 60 * 60
        await _redis_client.setex(key, ttl_seconds, "valid")
        logger.debug(f"Stored refresh token for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to store refresh token: {e}")
        return False


async def validate_refresh_token(user_id: str, jti: str) -> bool:
    """
    Check if a refresh token exists in Redis (is valid).

    Args:
        user_id: The user's ID
        jti: The token's unique identifier

    Returns:
        True if token is valid
    """
    if _redis_client is None:
        logger.warning("Redis not connected, cannot validate refresh token")
        return False

    try:
        key = _get_refresh_token_key(user_id, jti)
        exists = await _redis_client.exists(key)
        return bool(exists)
    except Exception as e:
        logger.error(f"Failed to validate refresh token: {e}")
        return False


async def revoke_refresh_token(user_id: str, jti: str) -> bool:
    """
    Revoke (delete) a specific refresh token.

    Args:
        user_id: The user's ID
        jti: The token's unique identifier

    Returns:
        True if revoked successfully
    """
    if _redis_client is None:
        logger.warning("Redis not connected, cannot revoke refresh token")
        return False

    try:
        key = _get_refresh_token_key(user_id, jti)
        deleted = await _redis_client.delete(key)
        if deleted:
            logger.debug(f"Revoked refresh token for user {user_id}")
        return bool(deleted)
    except Exception as e:
        logger.error(f"Failed to revoke refresh token: {e}")
        return False


async def revoke_all_user_tokens(user_id: str) -> int:
    """
    Revoke all refresh tokens for a user (logout from all devices).

    Args:
        user_id: The user's ID

    Returns:
        Number of tokens revoked
    """
    if _redis_client is None:
        logger.warning("Redis not connected, cannot revoke user tokens")
        return 0

    try:
        pattern = _get_user_tokens_pattern(user_id)
        keys = []
        async for key in _redis_client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await _redis_client.delete(*keys)
            logger.info(f"Revoked {deleted} refresh tokens for user {user_id}")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Failed to revoke user tokens: {e}")
        return 0
