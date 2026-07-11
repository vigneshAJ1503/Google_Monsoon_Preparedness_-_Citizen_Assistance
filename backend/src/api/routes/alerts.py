"""Active alerts endpoint - deterministic NDMA warning feed integration.

Integrates verified official NDMA warning feeds with deterministic trigger logic.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.rate_limiter import check_rate_limit
from src.application.alert_service import alert_service
from src.application.translation_service import translation_service
from src.domain.models.alert import Alert
from src.infrastructure.persistence.database import get_db_session
from src.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "",
    summary="Get active weather and emergency alerts for a location",
    dependencies=[Depends(check_rate_limit)],
)
async def get_active_alerts(
    _request: Request,
    latitude: Annotated[float, Query(ge=-90, le=90, description="Latitude")],
    longitude: Annotated[float, Query(ge=-180, le=180, description="Longitude")],
    language: Annotated[
        str | None, Query(pattern="^(en|ta|hi)$", description="Language"),
    ] = "en",
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[Alert]:
    """Retrieve deterministic triggered alerts for a location.

    Integrates verified official NDMA warning feeds.
    Translates response alert texts to Tamil/Hindi if requested.
    """
    # 1. Fetch alerts
    alerts = await alert_service.get_alerts_for_location(latitude, longitude, db)

    # 2. Handle translations
    if language != "en" and alerts:
        logger.info("translating_active_alerts", lang=language, count=len(alerts))
        for alert in alerts:
            alert.title = await translation_service.translate_text(alert.title, language)
            alert.description = await translation_service.translate_text(
                alert.description, language,
            )
            if alert.citizen_message:
                alert.citizen_message = await translation_service.translate_text(
                    alert.citizen_message, language,
                )

    return alerts
