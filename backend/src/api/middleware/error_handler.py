"""
Middleware: global exception handler.
Maps domain exceptions to safe user-facing HTTP responses.
Per spec: 'Never expose malformed AI output directly.'
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions.weather import (
    WeatherProviderUnavailable,
    StaleWeatherData,
    UnsupportedLocation,
)
from src.domain.exceptions.llm import (
    InvalidAIResponse,
    LLMTimeout,
    SafetyValidationFailed,
)
from src.domain.exceptions.validation import (
    InvalidInput,
    UnsupportedLanguage,
    AlertSourceUnavailable,
)
from src.observability.logger import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI):
    """Register all domain exception handlers."""

    @app.exception_handler(WeatherProviderUnavailable)
    async def handle_weather_unavailable(request: Request, exc: WeatherProviderUnavailable):
        logger.warning("weather_provider_unavailable", provider=exc.provider, reason=exc.reason)
        return JSONResponse(
            status_code=503,
            content={
                "error": "weather_unavailable",
                "message": "Live weather data is currently unavailable. Safety recommendations requiring current conditions may be limited.",
                "data_available": False,
            },
        )

    @app.exception_handler(StaleWeatherData)
    async def handle_stale_data(request: Request, exc: StaleWeatherData):
        logger.warning("stale_weather_data", age_seconds=exc.age_seconds)
        return JSONResponse(
            status_code=200,
            content={
                "error": "stale_data",
                "message": f"Weather data is {exc.age_seconds // 60} minutes old and may not reflect current conditions.",
                "data_available": True,
                "is_stale": True,
            },
        )

    @app.exception_handler(UnsupportedLocation)
    async def handle_unsupported_location(request: Request, exc: UnsupportedLocation):
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_location",
                "message": "The specified location is not within the supported coverage area.",
            },
        )

    @app.exception_handler(InvalidAIResponse)
    async def handle_invalid_ai(request: Request, exc: InvalidAIResponse):
        # Never expose raw AI output to the user
        logger.error("invalid_ai_response", reason=exc.reason)
        return JSONResponse(
            status_code=500,
            content={
                "error": "ai_generation_failed",
                "message": "Unable to generate a response at this time. Please try again.",
            },
        )

    @app.exception_handler(LLMTimeout)
    async def handle_llm_timeout(request: Request, exc: LLMTimeout):
        logger.error("llm_timeout", timeout_seconds=exc.timeout_seconds)
        return JSONResponse(
            status_code=504,
            content={
                "error": "ai_timeout",
                "message": "The AI service is taking longer than expected. Please try again.",
            },
        )

    @app.exception_handler(SafetyValidationFailed)
    async def handle_safety_failure(request: Request, exc: SafetyValidationFailed):
        logger.error("safety_validation_failed", violations=exc.violations)
        return JSONResponse(
            status_code=500,
            content={
                "error": "safety_check_failed",
                "message": "The response could not be verified for safety. Please rephrase your question.",
            },
        )

    @app.exception_handler(InvalidInput)
    async def handle_invalid_input(request: Request, exc: InvalidInput):
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_input",
                "message": f"Invalid value for '{exc.field}': {exc.reason}",
            },
        )

    @app.exception_handler(UnsupportedLanguage)
    async def handle_unsupported_language(request: Request, exc: UnsupportedLanguage):
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_language",
                "message": f"Language '{exc.language_code}' is not supported.",
                "supported_languages": exc.supported,
            },
        )

    @app.exception_handler(AlertSourceUnavailable)
    async def handle_alert_source(request: Request, exc: AlertSourceUnavailable):
        logger.warning("alert_source_unavailable", source=exc.source)
        return JSONResponse(
            status_code=503,
            content={
                "error": "alert_source_unavailable",
                "message": "Official alert data is temporarily unavailable.",
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Catch-all: never expose stack traces to users
        logger.error("unhandled_exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
