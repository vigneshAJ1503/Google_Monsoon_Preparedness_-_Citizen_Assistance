"""
Redis client and connection manager.
Provides caching functionality with TTL support.
"""

from typing import Optional
import redis.asyncio as aioredis
from src.config import settings
from src.observability.logger import get_logger

logger = get_logger(__name__)


class RedisManager:
    """Manages Redis connection lifecycle and caching operations."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if self._client is not None:
            return

        try:
            logger.info("connecting_to_redis", url=settings.redis_url)
            self._client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
            )
            # Test connection
            await self._client.ping()
            logger.info("redis_connected_successfully")
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            self._client = None

    async def disconnect(self):
        """Close Redis connection."""
        if self._client is None:
            return

        try:
            await self._client.close()
            logger.info("redis_disconnected")
        except Exception as e:
            logger.error("redis_disconnect_failed", error=str(e))
        finally:
            self._client = None

    @property
    def client(self) -> aioredis.Redis:
        """Get the active Redis client. Raises RuntimeError if not connected."""
        if self._client is None:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        return self._client is not None

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self.is_connected:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error("redis_get_failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL (seconds)."""
        if not self.is_connected:
            return False
        try:
            if ttl:
                await self._client.set(key, value, ex=ttl)
            else:
                await self._client.set(key, value)
            return True
        except Exception as e:
            logger.error("redis_set_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_connected:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error("redis_delete_failed", key=key, error=str(e))
            return False


# Singleton instance
redis_manager = RedisManager()
