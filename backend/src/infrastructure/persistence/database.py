"""
Database connection manager.
Provides async session maker and lifecycle hooks.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from src.config import settings
from src.observability.logger import get_logger

logger = get_logger(__name__)

# Declarative base for SQLAlchemy models
Base = declarative_base()


def _get_async_database_url() -> str:
    """Convert sync PostgreSQL URL to async URL for asyncpg."""
    url = settings.database_url
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class DatabaseManager:
    """Manages PostgreSQL connection lifecycle and async sessions."""

    def __init__(self):
        self._engine = None
        self._session_maker = None

    async def connect(self):
        """Initialize database engine and session maker."""
        if self._engine is not None:
            return

        try:
            async_url = _get_async_database_url()
            logger.info("connecting_to_database", url=async_url)
            self._engine = create_async_engine(
                async_url,
                echo=settings.is_development and settings.log_level == "DEBUG",
                future=True,
                pool_size=10,
                max_overflow=20,
            )
            self._session_maker = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
            logger.info("database_connected_successfully")
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise e

    async def disconnect(self):
        """Close database engine."""
        if self._engine is None:
            return

        try:
            await self._engine.dispose()
            logger.info("database_disconnected")
        except Exception as e:
            logger.error("database_disconnect_failed", error=str(e))
        finally:
            self._engine = None
            self._session_maker = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for getting db session in routes."""
        if self._session_maker is None:
            raise RuntimeError("Database not initialized. Call connect() first.")

        async with self._session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error("database_session_error", error=str(e))
                raise e


# Singleton instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI session dependency."""
    async for session in db_manager.get_session():
        yield session
