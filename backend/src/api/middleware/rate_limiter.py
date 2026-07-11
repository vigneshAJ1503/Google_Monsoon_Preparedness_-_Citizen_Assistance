"""Simple rate limiter using Redis."""

from fastapi import HTTPException, Request
from redis.exceptions import RedisError

from src.config import settings
from src.infrastructure.cache.redis_client import redis_manager
from src.observability.logger import get_logger

logger = get_logger(__name__)


async def check_rate_limit(request: Request) -> None:
    """Check if the client has exceeded the rate limit.

    Args:
        request: Incoming HTTP request

    """
    if not redis_manager.is_connected:
        # If Redis is down, allow the request (fail open for availability)
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"

    try:
        current = await redis_manager.client.incr(key)
        if current == 1:
            await redis_manager.client.expire(key, settings.rate_limit_window_seconds)

        if current > settings.rate_limit_requests:
            logger.warning("rate_limit_exceeded", client_ip=client_ip, count=current)
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )
    except HTTPException:
        raise
    except RedisError as e:
        # Rate limiting failure should not break the application
        logger.exception("rate_limit_error", error=str(e))
