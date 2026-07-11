"""FastAPI application entry point.
Registers middleware, routes, and lifecycle events.
"""

import os
import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import register_exception_handlers
from src.api.middleware.request_id import RequestIDMiddleware
from src.api.routes import (
    alerts,
    assistant,
    checklist,
    health,
    preparedness,
    travel,
    weather,
)
from src.config import settings
from src.infrastructure.cache.redis_client import redis_manager
from src.infrastructure.persistence.database import db_manager
from src.observability.logger import get_logger

logger = get_logger(__name__)


def run_migrations() -> None:
    """Run alembic migrations at startup."""
    try:
        logger.info("running_database_migrations")
        # Find alembic.ini - it's in /app/backend or /backend depending on container
        alembic_paths = ["/app/backend", "/backend", "/app"]
        alembic_dir = None
        for path in alembic_paths:
            if os.path.exists(os.path.join(path, "alembic.ini")):
                alembic_dir = path
                break
        
        if not alembic_dir:
            logger.error("alembic.ini_not_found")
            return
            
        logger.info("running_migrations_in", directory=alembic_dir)
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=alembic_dir,
        )
        if result.returncode != 0:
            logger.error("migration_failed", stderr=result.stderr, stdout=result.stdout)
        else:
            logger.info("migrations_completed", stdout=result.stdout)
    except Exception as e:
        logger.exception("migration_error", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info(
        "application_starting",
        environment=settings.app_env,
        debug=settings.app_debug,
    )

    # Initialize connections first
    await redis_manager.connect()
    await db_manager.connect()

    # Run database migrations after connection is established
    run_migrations()

    logger.info("application_ready")
    yield

    # Cleanup
    await redis_manager.disconnect()
    await db_manager.disconnect()
    logger.info("application_shutdown")


app = FastAPI(
    title="Monsoon Preparedness & Citizen Assistance",
    description=(
        "GenAI-powered monsoon preparedness application providing personalized safety guidance, "
        "weather-aware recommendations, emergency checklists, and real-time alerts for Indian citizens."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
)

# --- Middleware ---
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --- Exception Handlers ---
register_exception_handlers(app)

# --- Routes ---
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(
    preparedness.router, prefix="/api/preparedness", tags=["Preparedness"],
)
app.include_router(checklist.router, prefix="/api/checklist", tags=["Checklist"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["Assistant"])
app.include_router(travel.router, prefix="/api/travel", tags=["Travel"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
