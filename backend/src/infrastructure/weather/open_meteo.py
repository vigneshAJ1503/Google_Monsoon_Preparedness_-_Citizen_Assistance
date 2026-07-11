"""
Open-Meteo API client.
Fetches current weather, hourly forecast, and daily forecast.
Per spec: 'Cache responses with an explicit TTL. Apply timeout and retry policies to external API calls. Avoid uncontrolled retry loops.'
"""

import httpx
from datetime import datetime
from typing import Dict, Any, Optional

from src.config import settings
from src.domain.exceptions.weather import WeatherProviderUnavailable
from src.observability.logger import get_logger
from src.observability.metrics import timer, metrics

logger = get_logger(__name__)


class OpenMeteoClient:
    """Async client for the Open-Meteo API."""

    def __init__(self):
        self.base_url = settings.open_meteo_base_url
        self.client = httpx.AsyncClient(
            timeout=settings.weather_request_timeout_seconds,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def fetch_weather(self, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch current weather, daily forecast and hourly rain forecast."""
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "visibility",
                "pressure_msl",
                "cloud_cover",
                "soil_moisture_0_to_10cm",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "sunrise",
                "sunset",
            ],
            "hourly": "precipitation",
            "timezone": "auto",
            "forecast_days": 7,
        }

        url = f"{self.base_url}/forecast"
        
        # Bounded retry loop (per spec)
        retries = settings.weather_max_retries
        for attempt in range(retries + 1):
            try:
                logger.info(
                    "fetching_open_meteo_weather",
                    latitude=lat,
                    longitude=lng,
                    attempt=attempt,
                )
                with timer("open_meteo_request_duration"):
                    response = await self.client.get(url, params=params)
                
                if response.status_code == 200:
                    metrics.increment("open_meteo_success_rate")
                    return response.json()
                
                # Check for rate limiting
                if response.status_code == 429:
                    metrics.increment("open_meteo_rate_limits")
                    logger.warning("open_meteo_rate_limited", status_code=429)
                    if attempt == retries:
                        raise WeatherProviderUnavailable(
                            "Open-Meteo", f"Rate limited (status 429)"
                        )
                elif response.status_code >= 500:
                    metrics.increment("open_meteo_server_errors")
                    logger.warning(
                        "open_meteo_server_error",
                        status_code=response.status_code,
                        body=response.text,
                    )
                    if attempt == retries:
                        raise WeatherProviderUnavailable(
                            "Open-Meteo", f"Server error: {response.status_code}"
                        )
                else:
                    logger.error(
                        "open_meteo_invalid_request",
                        status_code=response.status_code,
                        body=response.text,
                    )
                    raise WeatherProviderUnavailable(
                        "Open-Meteo", f"Invalid request parameter or endpoint"
                    )

            except httpx.TimeoutException as e:
                metrics.increment("open_meteo_timeouts")
                logger.warning("open_meteo_timeout", attempt=attempt, error=str(e))
                if attempt == retries:
                    raise WeatherProviderUnavailable("Open-Meteo", "Connection timeout")
            
            except httpx.RequestError as e:
                metrics.increment("open_meteo_network_errors")
                logger.warning("open_meteo_network_error", attempt=attempt, error=str(e))
                if attempt == retries:
                    raise WeatherProviderUnavailable("Open-Meteo", f"Network error: {str(e)}")

        raise WeatherProviderUnavailable("Open-Meteo", "Max retries exceeded")

    async def close(self):
        """Close connection pools."""
        await self.client.aclose()


# Singleton client
open_meteo_client = OpenMeteoClient()
