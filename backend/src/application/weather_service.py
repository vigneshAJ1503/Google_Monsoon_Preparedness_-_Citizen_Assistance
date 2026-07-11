"""Weather service orchestrating retrieval, caching, normalization,
and monsoon phase determination.
"""

import json
from datetime import date, datetime, timezone

from src.config import settings
from src.domain.models.weather import (
    WeatherContext,
    WeatherForecast,
    WeatherObservation,
)
from src.domain.rules.monsoon_season import get_monsoon_phase, is_monsoon_season
from src.infrastructure.cache.redis_client import redis_manager
from src.infrastructure.geocoding.nominatim_client import nominatim_client
from src.infrastructure.weather.open_meteo import open_meteo_client
from src.infrastructure.weather.weather_normalizer import (
    normalize_forecast,
    normalize_observation,
)
from src.observability.logger import get_logger

logger = get_logger(__name__)


class WeatherService:
    """Orchestrates weather operations across caches and providers."""

    async def get_weather_context(
        self, lat: float, lng: float, bypass_cache: bool = False,
    ) -> WeatherContext:
        """Get combined weather context (observation + forecast + monsoon phase).
        Uses caching to avoid excessive external provider calls.
        """
        # Round coordinates for caching key stability (roughly ~1.1km grid)
        cache_lat = round(lat, 2)
        cache_lng = round(lng, 2)
        cache_key = f"weather_context:{cache_lat}:{cache_lng}"

        if not bypass_cache:
            cached = await redis_manager.get(cache_key)
            if cached:
                try:
                    logger.info(
                        "weather_context_cache_hit", lat=cache_lat, lng=cache_lng,
                    )
                    data = json.loads(cached)
                    context = WeatherContext(**data)

                    # Verify freshness of cached context
                    obs_time = context.current.observed_at
                    now = datetime.now(timezone.utc)
                    # Ensure obs_time is timezone-aware
                    if obs_time.tzinfo is None:
                        obs_time = obs_time.replace(tzinfo=timezone.utc)
                    age_seconds = int((now - obs_time).total_seconds())

                    if age_seconds > settings.weather_stale_threshold_seconds:
                        logger.warning("cached_weather_stale", age_seconds=age_seconds)
                        # We continue and update instead of raising StaleWeatherData to keep app available
                    else:
                        return context
                except Exception as e:
                    logger.exception("parse_cached_weather_error", error=str(e))

        try:
            # 1. Fetch raw weather from Open-Meteo
            raw_data = await open_meteo_client.fetch_weather(lat, lng)

            # 2. Convert to domain objects
            observation = normalize_observation(raw_data)
            forecast = normalize_forecast(raw_data)

            # 3. Resolve location details (state, etc.) for monsoon detection
            location_details = await nominatim_client.reverse_geocode(lat, lng)
            state_name = location_details.state if location_details else None
            location_name = location_details.name if location_details else None

            observation.location_name = location_name
            forecast.location_name = location_name

            # 4. Check active monsoon phase
            check_date = date.today()
            is_monsoon = is_monsoon_season(check_date, state=state_name, latitude=lat)
            phase = get_monsoon_phase(check_date, state=state_name, latitude=lat)

            # 5. Build context
            context = WeatherContext(
                current=observation,
                forecast=forecast,
                is_monsoon_season=is_monsoon,
                monsoon_phase=phase.value,
                data_available=True,
            )

            # 6. Cache the serialized result
            # Cache duration matches minimum of weather TTL settings
            await redis_manager.set(
                cache_key,
                context.model_dump_json(),
                ttl=settings.weather_cache_ttl_seconds,
            )

            return context

        except Exception as e:
            logger.exception("weather_context_fetch_failed", error=str(e))
            # Return degraded state when provider fails
            return WeatherContext(
                current=WeatherObservation(
                    latitude=lat,
                    longitude=lng,
                    observed_at=datetime.now(timezone.utc),
                    condition="unknown",
                    rainfall={"current_mm": 0.0, "forecast_mm": 0.0},
                    wind={"speed_kmph": 0.0},
                    source="fallback",
                    data_age_seconds=0,
                ),
                forecast=WeatherForecast(
                    latitude=lat,
                    longitude=lng,
                    generated_at=datetime.now(timezone.utc),
                    days=[],
                    source="fallback",
                    data_age_seconds=0,
                ),
                is_monsoon_season=False,
                data_available=False,
                unavailability_reason="Live weather data is currently unavailable. Safety recommendations requiring current conditions may be limited.",
            )


# Singleton
weather_service = WeatherService()
