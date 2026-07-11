"""
Centralized application configuration.
All external config flows through Pydantic settings — no scattered env reads.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://monsoonprep:monsoonprep_dev_password@postgres:5432/monsoonprep",
        alias="DATABASE_URL",
    )

    # --- Redis ---
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # --- Gemini AI ---
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_timeout_seconds: int = Field(default=30, alias="GEMINI_TIMEOUT_SECONDS")
    gemini_max_output_tokens: int = Field(default=2048, alias="GEMINI_MAX_OUTPUT_TOKENS")

    # --- Groq AI (Free tier: 14,400 req/day for Llama 3.1 8B) ---
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    groq_timeout_seconds: int = Field(default=30, alias="GROQ_TIMEOUT_SECONDS")
    groq_max_output_tokens: int = Field(default=2048, alias="GROQ_MAX_OUTPUT_TOKENS")

    # --- Weather (Open-Meteo — no API key needed) ---
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1"
    weather_cache_ttl_seconds: int = Field(default=300, alias="WEATHER_CACHE_TTL_SECONDS")
    forecast_cache_ttl_seconds: int = Field(default=1800, alias="FORECAST_CACHE_TTL_SECONDS")
    weather_request_timeout_seconds: int = 10
    weather_max_retries: int = 2
    weather_stale_threshold_seconds: int = 600

    # --- Alert Engine ---
    alert_cooldown_minutes: int = Field(default=180, alias="ALERT_COOLDOWN_MINUTES")
    alert_data_max_age_seconds: int = Field(default=600, alias="ALERT_DATA_MAX_AGE_SECONDS")
    alert_poll_interval_seconds: int = 300

    # --- Geocoding (Nominatim — no API key needed) ---
    nominatim_user_agent: str = "monsoonprep-app/1.0"
    geocoding_cache_ttl_seconds: int = 86400  # 24 hours

    # --- Rate Limiting ---
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # --- CORS ---
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://localhost:80",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance
settings = Settings()
