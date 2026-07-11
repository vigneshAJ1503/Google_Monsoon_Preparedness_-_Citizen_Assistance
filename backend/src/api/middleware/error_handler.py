"""Middleware: global exception handler.

Maps domain exceptions to safe user-facing HTTP responses.

Per spec: "Never expose malformed AI output directly."
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.domain.exceptions.llm import (
    InvalidAIResponse,
    LLMTimeout,
    SafetyValidationFailed,
)
from src.domain.exceptions.validation import (
    AlertSourceUnavailable,
    InvalidInput,
    UnsupportedLanguage,
)
from src.domain.exceptions.weather import (
    StaleWeatherData,
    UnsupportedLocation,
    WeatherProviderUnavailable,
)
from src.observability.logger import get_logger

logger = get_logger(__name__)


def _build_weather_unavailable_response(exc: WeatherProviderUnavailable) -> JSONResponse:
    logger.warning("weather_provider_unavailable", provider=exc.provider, reason=exc.reason)
    return JSONResponse(
        status_code=503,
        content={
            "error": "weather_unavailable",
            "message": (
                "Live weather data is currently unavailable. "
                "Safety recommendations requiring current conditions may be limited."
            ),
            "data_available": False,
        },
    )


def _build_stale_data_response(exc: StaleWeatherData) -> JSONResponse:
    logger.warning("stale_weather_data", age_seconds=exc.age_seconds)
    return JSONResponse(
        status_code=200,
        content={
            "error": "stale_data",
            "message": (
                f"Weather data is {exc.age_seconds // 60} minutes old "
                "and may not reflect current conditions."
            ),
            "data_available": True,
            "is_stale": True,
        },
    )


def _build_unsupported_location_response(_exc: UnsupportedLocation) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "unsupported_location",
            "message": "The specified location is not within the supported coverage area.",
        },
    )


def _build_invalid_ai_response(exc: InvalidAIResponse) -> JSONResponse:
    logger.error("invalid_ai_response", reason=exc.reason)
    return JSONResponse(
        status_code=500,
        content={
            "error": "ai_generation_failed",
            "message": "Unable to generate a response at this time. Please try again.",
        },
    )


def _build_llm_timeout_response(exc: LLMTimeout) -> JSONResponse:
    logger.error("llm_timeout", timeout_seconds=exc.timeout_seconds)
    return JSONResponse(
        status_code=504,
        content={
            "error": "ai_timeout",
            "message": "The AI service is taking longer than expected. Please try again.",
        },
    )


def _build_safety_failure_response(exc: SafetyValidationFailed) -> JSONResponse:
    logger.error("safety_validation_failed", violations=exc.violations)
    return JSONResponse(
        status_code=500,
        content={
            "error": "safety_check_failed",
            "message": (
                "The response could not be verified for safety. "
                "Please rephrase your question."
            ),
        },
    )


def _build_invalid_input_response(exc: InvalidInput) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_input",
            "message": f"Invalid value for '{exc.field}': {exc.reason}",
        },
    )


def _build_unsupported_language_response(exc: UnsupportedLanguage) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "unsupported_language",
            "message": f"Language '{exc.language_code}' is not supported.",
            "supported_languages": exc.supported,
        },
    )


def _build_alert_source_unavailable_response(exc: AlertSourceUnavailable) -> JSONResponse:
    logger.warning("alert_source_unavailable", source=exc.source)
    return JSONResponse(
        status_code=503,
        content={
            "error": "alert_source_unavailable",
            "message": "Official alert data is temporarily unavailable.",
        },
    )


def _build_unexpected_error_response(exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers."""
    app.exception_handler(WeatherProviderUnavailable)(_build_weather_unavailable_response)
    app.exception_handler(StaleWeatherData)(_build_stale_data_response)
    app.exception_handler(UnsupportedLocation)(_build_unsupported_location_response)
    app.exception_handler(InvalidAIResponse)(_build_invalid_ai_response)
    app.exception_handler(LLMTimeout)(_build_llm_timeout_response)
    app.exception_handler(SafetyValidationFailed)(_build_safety_failure_response)
    app.exception_handler(InvalidInput)(_build_invalid_input_response)
    app.exception_handler(UnsupportedLanguage)(_build_unsupported_language_response)
    app.exception_handler(AlertSourceUnavailable)(_build_alert_source_unavailable_response)
    app.exception_handler(Exception)(_build_unexpected_error_response)
