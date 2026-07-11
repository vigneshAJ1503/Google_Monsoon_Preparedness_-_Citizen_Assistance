"""Weather endpoints.

Provides normalized current weather and multi-day forecasts.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from src.api.middleware.rate_limiter import check_rate_limit
from src.application.weather_service import weather_service
from src.domain.exceptions.validation import InvalidInput
from src.domain.models.weather import WeatherContext

router = APIRouter()


@router.get(
    "",
    summary="Get weather and monsoon context for a location",
    dependencies=[Depends(check_rate_limit)],
)
async def get_weather(
    _request: Request,
    latitude: Annotated[float, Query(description="Latitude coordinate (-90 to 90)")],
    longitude: Annotated[float, Query(description="Longitude coordinate (-180 to 180)")],
    bypass_cache: Annotated[bool, Query(description="Force refresh from upstream API")] = False,
) -> WeatherContext:
    """Fetch normalized current weather conditions and forecasts for a coordinate.

    Validates latitude and longitude ranges.
    """
    if not -90 <= latitude <= 90:
        msg = "latitude"
        raise InvalidInput(msg, "Must be between -90 and 90")
    if not -180 <= longitude <= 180:
        msg = "longitude"
        raise InvalidInput(msg, "Must be between -180 and 180")

    return await weather_service.get_weather_context(
        latitude, longitude, bypass_cache=bypass_cache,
    )
