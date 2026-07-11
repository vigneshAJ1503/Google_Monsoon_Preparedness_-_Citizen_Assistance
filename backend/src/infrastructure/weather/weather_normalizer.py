"""Normalize Open-Meteo responses to domain Weather models.
Maps WMO codes to WeatherCondition enum.
"""

from datetime import datetime, timezone
from typing import Any

from src.domain.models.weather import (
    ForecastDay,
    RainfallData,
    WeatherCondition,
    WeatherForecast,
    WeatherObservation,
    WindData,
)


def map_wmo_code(code: int) -> WeatherCondition:
    """Map WMO (World Meteorological Organization) weather code to domain Enum."""
    # WMO weather interpretation codes: https://open-meteo.com/en/docs
    if code == 0:
        return WeatherCondition.CLEAR
    if code in (1, 2):
        return WeatherCondition.PARTLY_CLOUDY
    if code == 3:
        return WeatherCondition.CLOUDY
    if code in (45, 48):
        return WeatherCondition.FOG
    if code in (51, 53, 55, 56, 57):
        return WeatherCondition.DRIZZLE
    if code in (61, 80):
        return WeatherCondition.LIGHT_RAIN
    if code in (63, 66, 67, 81):
        return WeatherCondition.MODERATE_RAIN
    if code == 65:
        return WeatherCondition.HEAVY_RAIN
    if code == 82:
        return WeatherCondition.VERY_HEAVY_RAIN  # Violent rain showers
    if code in (95, 96, 99):
        return WeatherCondition.THUNDERSTORM
    return WeatherCondition.UNKNOWN


def normalize_observation(raw: dict[str, Any]) -> WeatherObservation:
    """Map Open-Meteo JSON into WeatherObservation domain model."""
    current = raw.get("current", {})
    hourly = raw.get("hourly", {})

    # Calculate 24h forecast sum from hourly values
    hourly_precip = hourly.get("precipitation", [])
    forecast_24h_mm = sum(hourly_precip[:24]) if hourly_precip else 0.0

    current_time_str = current.get("time")
    if current_time_str:
        current_time = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
        # Ensure timezone-aware
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
    else:
        current_time = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    age_seconds = int((now - current_time).total_seconds())

    return WeatherObservation(
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        observed_at=current_time,
        condition=map_wmo_code(current.get("weather_code", 0)),
        temperature_celsius=current.get("temperature_2m"),
        feels_like_celsius=current.get("apparent_temperature"),
        humidity_percent=current.get("relative_humidity_2m"),
        rainfall=RainfallData(
            current_mm=current.get("precipitation", 0.0),
            forecast_mm=forecast_24h_mm,
            hourly_forecast=hourly_precip[:24] if hourly_precip else [],
        ),
        wind=WindData(
            speed_kmph=current.get("wind_speed_10m", 0.0),
            gust_kmph=current.get("wind_gusts_10m"),
            direction_degrees=current.get("wind_direction_10m"),
        ),
        visibility_km=(
            current.get("visibility", 10000.0) / 1000.0
            if "visibility" in current
            else None
        ),
        pressure_hpa=current.get("pressure_msl"),
        cloud_cover_percent=current.get("cloud_cover"),
        soil_moisture=current.get("soil_moisture_0_to_10cm"),
        source="Open-Meteo",
        data_age_seconds=max(0, age_seconds),
        is_stale=False,  # Calculated at service layer depending on threshold
    )


def normalize_forecast(raw: dict[str, Any]) -> WeatherForecast:
    """Map Open-Meteo JSON into WeatherForecast domain model."""
    daily = raw.get("daily", {})
    days = []

    # Map daily lists into ForecastDay items
    times = daily.get("time", [])
    for idx, time_str in enumerate(times):
        days.append(
            ForecastDay(
                date=time_str,
                condition=map_wmo_code(daily.get("weather_code", [0])[idx]),
                temp_min_celsius=daily.get("temperature_2m_min", [None])[idx],
                temp_max_celsius=daily.get("temperature_2m_max", [None])[idx],
                rainfall_mm=daily.get("precipitation_sum", [0.0])[idx],
                rainfall_probability_percent=daily.get(
                    "precipitation_probability_max", [None],
                )[idx],
                wind_speed_kmph=daily.get("wind_speed_10m_max", [0.0])[idx],
                wind_gust_kmph=daily.get("wind_gusts_10m_max", [None])[idx],
                sunrise=daily.get("sunrise", [None])[idx],
                sunset=daily.get("sunset", [None])[idx],
            ),
        )

    now = datetime.now(timezone.utc)
    current_time_str = raw.get("current", {}).get("time", "")
    if current_time_str:
        current_time = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        age_seconds = int((now - current_time).total_seconds())
    else:
        age_seconds = 0

    return WeatherForecast(
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        generated_at=now,
        days=days,
        source="Open-Meteo",
        data_age_seconds=age_seconds,
        is_stale=False,
    )
