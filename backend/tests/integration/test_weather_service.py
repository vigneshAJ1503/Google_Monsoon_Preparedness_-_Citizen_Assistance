"""
Integration tests for Weather Service.
Mocks external network calls to Open-Meteo.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from src.application.weather_service import weather_service
from src.domain.models.weather import WeatherContext, WeatherCondition


@pytest.mark.asyncio
async def test_get_weather_context_success():
    # Mock data return from Open-Meteo client
    mock_raw = {
        "latitude": 11.01,
        "longitude": 76.95,
        "current": {
            "time": "2026-07-11T12:00:00Z",
            "weather_code": 3,
            "temperature_2m": 25.0,
            "precipitation": 0.0,
            "wind_speed_10m": 12.0,
        },
        "daily": {
            "time": ["2026-07-11"],
            "weather_code": [3],
            "precipitation_sum": [0.0],
            "wind_speed_10m_max": [15.0],
        },
        "hourly": {
            "time": ["2026-07-11T12:00:00Z"],
            "precipitation": [0.0],
        }
    }

    # Patch open_meteo_client fetch call
    with patch("src.application.weather_service.open_meteo_client.fetch_weather", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_raw
        
        # Patch nominatim reverse geocoding to avoid network call
        with patch("src.application.weather_service.nominatim_client.reverse_geocode", new_callable=AsyncMock) as mock_geo:
            mock_geo.return_value = None
            
            context = await weather_service.get_weather_context(11.01, 76.95, bypass_cache=True)
            
            assert context.data_available is True
            assert context.current.latitude == 11.01
            assert context.current.condition == WeatherCondition.CLOUDY
            assert context.current.temperature_celsius == 25.0
            mock_fetch.assert_called_once_with(11.01, 76.95)


@pytest.mark.asyncio
async def test_get_weather_context_provider_failure():
    # Mock Open-Meteo failure
    with patch("src.application.weather_service.open_meteo_client.fetch_weather", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = Exception("API Server is down")
        
        context = await weather_service.get_weather_context(11.01, 76.95, bypass_cache=True)
        
        # Should degrade safely and return a placeholder condition instead of raising exceptions
        assert context.data_available is False
        assert context.current.condition == WeatherCondition.UNKNOWN
        assert "Live weather data is currently unavailable" in context.unavailability_reason
