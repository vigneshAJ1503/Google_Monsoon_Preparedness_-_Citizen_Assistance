"""
Unit tests for weather normalizer.
"""

from datetime import datetime, timezone
from src.infrastructure.weather.weather_normalizer import map_wmo_code, normalize_observation, normalize_forecast
from src.domain.models.weather import WeatherCondition


def test_map_wmo_code():
    assert map_wmo_code(0) == WeatherCondition.CLEAR
    assert map_wmo_code(1) == WeatherCondition.PARTLY_CLOUDY
    assert map_wmo_code(3) == WeatherCondition.CLOUDY
    assert map_wmo_code(45) == WeatherCondition.FOG
    assert map_wmo_code(51) == WeatherCondition.DRIZZLE
    assert map_wmo_code(61) == WeatherCondition.LIGHT_RAIN
    assert map_wmo_code(63) == WeatherCondition.MODERATE_RAIN
    assert map_wmo_code(65) == WeatherCondition.HEAVY_RAIN
    assert map_wmo_code(82) == WeatherCondition.VERY_HEAVY_RAIN
    assert map_wmo_code(95) == WeatherCondition.THUNDERSTORM
    assert map_wmo_code(99) == WeatherCondition.THUNDERSTORM
    assert map_wmo_code(12345) == WeatherCondition.UNKNOWN


def test_normalize_observation():
    raw = {
        "latitude": 11.0168,
        "longitude": 76.9558,
        "current": {
            "time": "2026-07-11T12:00:00Z",
            "weather_code": 95,
            "temperature_2m": 28.5,
            "apparent_temperature": 32.0,
            "relative_humidity_2m": 85,
            "precipitation": 12.5,
            "wind_speed_10m": 45.0,
            "wind_gusts_10m": 65.0,
            "wind_direction_10m": 240.0,
            "visibility": 8000.0,
            "pressure_msl": 1008.0,
            "cloud_cover": 90,
            "soil_moisture_0_to_10cm": 0.35,
        },
        "hourly": {
            "time": [f"2026-07-11T{i:02d}:00:00Z" for i in range(24)],
            "precipitation": [2.5] * 24,
        },
    }

    obs = normalize_observation(raw)
    assert obs.latitude == 11.0168
    assert obs.longitude == 76.9558
    assert obs.condition == WeatherCondition.THUNDERSTORM
    assert obs.temperature_celsius == 28.5
    assert obs.feels_like_celsius == 32.0
    assert obs.humidity_percent == 85
    assert obs.rainfall.current_mm == 12.5
    # 24 hours of 2.5mm = 60.0mm
    assert obs.rainfall.forecast_mm == 60.0
    assert obs.wind.speed_kmph == 45.0
    assert obs.wind.gust_kmph == 65.0
    assert obs.wind.direction_degrees == 240.0
    assert obs.visibility_km == 8.0
    assert obs.pressure_hpa == 1008.0
    assert obs.cloud_cover_percent == 90
    assert obs.soil_moisture == 0.35
    assert obs.source == "Open-Meteo"
    assert obs.is_stale is False
