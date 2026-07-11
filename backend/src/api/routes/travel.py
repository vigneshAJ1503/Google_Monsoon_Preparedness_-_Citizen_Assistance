"""Travel Advisory endpoints.

Provides weather-aware routing safety advisories.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.rate_limiter import check_rate_limit
from src.application.translation_service import translation_service
from src.application.travel_service import travel_service
from src.domain.models.travel import TravelAdvisory
from src.infrastructure.persistence.database import get_db_session
from src.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class TravelAdvisoryRequest(BaseModel):
    """Request body for travel advisory."""

    origin_lat: float = Field(..., ge=-90, le=90, description="Origin latitude")
    origin_lng: float = Field(..., ge=-180, le=180, description="Origin longitude")
    dest_lat: float = Field(..., ge=-90, le=90, description="Destination latitude")
    dest_lng: float = Field(..., ge=-180, le=180, description="Destination longitude")
    preferred_language: str | None = Field("en", pattern="^(en|ta|hi)$")


@router.post(
    "/advisory",
    summary="Get route travel safety advisory",
    dependencies=[Depends(check_rate_limit)],
)
async def get_travel_advisory(
    _request: Request,
    body: TravelAdvisoryRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TravelAdvisory:
    """Generate travel safety analysis between two points.

    Analyzes weather forecasts and alerts.
    Translates output if Tamil or Hindi is preferred.
    """
    # 1. Evaluate safety
    advisory = await travel_service.get_travel_advisory(
        origin_lat=body.origin_lat,
        origin_lng=body.origin_lng,
        dest_lat=body.dest_lat,
        dest_lng=body.dest_lng,
        db=db,
    )

    # 2. Translate if required
    lang = body.preferred_language
    if lang != "en":
        logger.info("translating_travel_advisory", lang=lang)

        # Translate risk reasons
        translated_reasons = []
        for reason in advisory.risk_reasons:
            translated_reasons.append(await translation_service.translate_text(reason, lang))
        advisory.risk_reasons = translated_reasons

        # Translate recommendations
        translated_recs = []
        for rec in advisory.recommendations:
            translated_recs.append(await translation_service.translate_text(rec, lang))
        advisory.recommendations = translated_recs

        # Translate limitations
        translated_lims = []
        for lim in advisory.limitations:
            translated_lims.append(await translation_service.translate_text(lim, lang))
        advisory.limitations = translated_lims

    return advisory
