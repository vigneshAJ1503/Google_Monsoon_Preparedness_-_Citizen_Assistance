"""
Health check route.
Checks connections to PostgreSQL, Redis, and external APIs.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.cache.redis_client import redis_manager
from src.config import settings

router = APIRouter()


@router.get("/health", summary="Application health check")
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Check status of database, cache, and configuration."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        if redis_manager.is_connected:
            await redis_manager.client.ping()
            redis_ok = True
    except Exception:
        pass

    gemini_key_set = settings.gemini_api_key is not None and settings.gemini_api_key != ""

    status = "healthy" if db_ok and redis_ok else "unhealthy"
    
    return {
        "status": status,
        "database": "connected" if db_ok else "disconnected",
        "cache": "connected" if redis_ok else "disconnected",
        "gemini_api": "configured" if gemini_key_set else "missing_key",
        "environment": settings.app_env,
    }
