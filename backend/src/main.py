"""FastAPI application entry point.
Registers middleware, routes, and lifecycle events.
"""

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info(
        "application_starting",
        environment=settings.app_env,
        debug=settings.app_debug,
    )

    # Initialize connections
    await redis_manager.connect()
    await db_manager.connect()

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
