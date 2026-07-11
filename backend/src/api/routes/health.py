"""Health check route.

Checks connections to PostgreSQL, Redis, and external APIs.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.cache.redis_client import redis_manager
from src.infrastructure.persistence.database import get_db_session

router = APIRouter()


@router.get("/health", summary="Application health check")
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Check status of database, cache, and configuration."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError:
        pass

    redis_ok = False
    try:
        if redis_manager.is_connected:
            await redis_manager.client.ping()
            redis_ok = True
    except RedisError:
        pass

    groq_key_set = (
        settings.groq_api_key is not None and settings.groq_api_key != ""
    )

    status = "healthy" if db_ok and redis_ok else "unhealthy"

    return {
        "status": status,
        "database": "connected" if db_ok else "disconnected",
        "cache": "connected" if redis_ok else "disconnected",
        "groq_api": "configured" if groq_key_set else "missing_key",
        "environment": settings.app_env,
    }
