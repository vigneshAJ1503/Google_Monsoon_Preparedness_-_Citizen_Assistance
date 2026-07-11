"""
Weather domain models.
Internal representation — decoupled from any external API format.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    VERY_HEAVY_RAIN = "very_heavy_rain"
    EXTREMELY_HEAVY_RAIN = "extremely_heavy_rain"
    THUNDERSTORM = "thunderstorm"
    DRIZZLE = "drizzle"
    FOG = "fog"
    UNKNOWN = "unknown"


class RainfallData(BaseModel):
    """Rainfall measurements in millimeters."""
    current_mm: float = Field(ge=0, description="Current/recent rainfall in mm")
    forecast_mm: float = Field(ge=0, description="Forecast rainfall in mm for next 24h")
    hourly_forecast: list[float] = Field(default_factory=list, description="Hourly rainfall forecast (mm)")


class WindData(BaseModel):
    speed_kmph: float = Field(ge=0)
    gust_kmph: Optional[float] = Field(default=None, ge=0)
    direction_degrees: Optional[float] = Field(default=None, ge=0, le=360)


class WeatherObservation(BaseModel):
    """
    Normalized weather observation — the single internal representation
    used across ALL features: dashboard, alerts, plans, travel, assistant.
    Per spec: 'Create a normalized weather context and reuse it.'
    """
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: Optional[str] = None
    observed_at: datetime
    condition: WeatherCondition
    temperature_celsius: Optional[float] = None
    feels_like_celsius: Optional[float] = None
    humidity_percent: Optional[float] = Field(default=None, ge=0, le=100)
    rainfall: RainfallData
    wind: WindData
    visibility_km: Optional[float] = None
    pressure_hpa: Optional[float] = None
    uv_index: Optional[float] = None
    cloud_cover_percent: Optional[float] = Field(default=None, ge=0, le=100)
    soil_moisture: Optional[float] = None
    source: str = Field(description="Data provider name")
    data_age_seconds: int = Field(ge=0, description="Seconds since data was observed")
    is_stale: bool = Field(default=False, description="True if data exceeds staleness threshold")


class ForecastDay(BaseModel):
    """Single day forecast."""
    date: str  # ISO date string
    condition: WeatherCondition
    temp_min_celsius: Optional[float] = None
    temp_max_celsius: Optional[float] = None
    rainfall_mm: float = Field(ge=0)
    rainfall_probability_percent: Optional[float] = Field(default=None, ge=0, le=100)
    wind_speed_kmph: float = Field(ge=0)
    wind_gust_kmph: Optional[float] = None
    humidity_percent: Optional[float] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None


class WeatherForecast(BaseModel):
    """Multi-day weather forecast."""
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    generated_at: datetime
    days: list[ForecastDay]
    source: str
    data_age_seconds: int
    is_stale: bool = False


class WeatherContext(BaseModel):
    """
    Combined current + forecast weather context.
    This is the single object passed to all services that need weather data.
    """
    current: WeatherObservation
    forecast: WeatherForecast
    is_monsoon_season: bool = False
    monsoon_phase: Optional[str] = None  # pre_monsoon, active, retreating, post_monsoon
    data_available: bool = True
    unavailability_reason: Optional[str] = None
