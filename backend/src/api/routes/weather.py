"""
Weather endpoints.
Provides normalized current weather and multi-day forecasts.
"""

from fastapi import APIRouter, Query, Depends, Request

from src.api.middleware.rate_limiter import check_rate_limit
from src.application.weather_service import weather_service
from src.domain.models.weather import WeatherContext
from src.domain.exceptions.validation import InvalidInput

router = APIRouter()


@router.get(
    "",
    response_model=WeatherContext,
    summary="Get weather and monsoon context for a location",
    dependencies=[Depends(check_rate_limit)],
)
async def get_weather(
    request: Request,
    latitude: float = Query(..., description="Latitude coordinate (-90 to 90)"),
    longitude: float = Query(..., description="Longitude coordinate (-180 to 180)"),
    bypass_cache: bool = Query(False, description="Force refresh from upstream API"),
):
    """
    Fetch normalized current weather conditions and forecasts for a coordinate.
    Validates latitude and longitude ranges.
    """
    if not -90 <= latitude <= 90:
        raise InvalidInput("latitude", "Must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise InvalidInput("longitude", "Must be between -180 and 180")

    return await weather_service.get_weather_context(
        latitude, longitude, bypass_cache=bypass_cache
    )
