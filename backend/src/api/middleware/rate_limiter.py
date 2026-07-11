"""
Simple rate limiter using Redis.
"""

from fastapi import Request, HTTPException
from src.infrastructure.cache.redis_client import redis_manager
from src.config import settings
from src.observability.logger import get_logger

logger = get_logger(__name__)


async def check_rate_limit(request: Request):
    """Check if the client has exceeded the rate limit."""
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
    except Exception as e:
        # Rate limiting failure should not break the application
        logger.error("rate_limit_error", error=str(e))
