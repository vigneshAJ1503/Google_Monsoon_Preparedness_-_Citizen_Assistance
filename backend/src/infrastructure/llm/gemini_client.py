"""
Google Gemini API client using the new google-genai SDK.
Handles structured JSON output and error retry fallbacks.
"""

from typing import Type, TypeVar, Optional, Any
import json
import asyncio
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.config import settings
from src.domain.exceptions.llm import LLMTimeout, InvalidAIResponse, SafetyValidationFailed
from src.observability.logger import get_logger
from src.observability.metrics import timer, metrics

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Async wrapper for the Google Gemini API client."""

    def __init__(self):
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Lazy initialization of the Gemini Client."""
        if self._client is not None:
            return self._client

        if not settings.gemini_api_key:
            logger.warning("gemini_api_key_missing", message="Gemini API requests will fallback to deterministic generation")
            return None

        try:
            self._client = genai.Client(api_key=settings.gemini_api_key)
            return self._client
        except Exception as e:
            logger.error("gemini_client_init_failed", error=str(e))
            return None

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        max_retries: int = 1,
    ) -> T:
        """
        Generate structured output adhering to a Pydantic schema.
        Retries once if validation fails.
        """
        client = self._get_client()
        if not client:
            raise InvalidAIResponse("Gemini API key is not configured")

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction,
            temperature=0.2,  # Lower temperature for facts and safety compliance
            max_output_tokens=settings.gemini_max_output_tokens,
        )

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "calling_gemini_api",
                    model=settings.gemini_model,
                    schema=response_schema.__name__,
                    attempt=attempt,
                )
                
                # Execute asynchronously with timeout
                with timer("gemini_generation_duration"):
                    # google-genai async call: client.aio.models.generate_content
                    # Wait, let's wrap it in asyncio.wait_for to enforce settings.gemini_timeout_seconds
                    task = client.aio.models.generate_content(
                        model=settings.gemini_model,
                        contents=prompt,
                        config=config,
                    )
                    response = await asyncio.wait_for(task, timeout=settings.gemini_timeout_seconds)

                metrics.increment("gemini_success_rate")
                
                # Parse JSON output and return as schema
                if response.text:
                    try:
                        parsed_data = json.loads(response.text)
                        validated_obj = response_schema.model_validate(parsed_data)
                        return validated_obj
                    except Exception as e:
                        logger.warning(
                            "gemini_schema_validation_failed",
                            attempt=attempt,
                            error=str(e),
                            text=response.text,
                        )
                        metrics.increment("gemini_schema_failures")
                        if attempt == max_retries:
                            raise InvalidAIResponse(f"Schema validation failed: {str(e)}", response.text)
                else:
                    raise InvalidAIResponse("Empty response text from model")

            except asyncio.TimeoutError:
                metrics.increment("gemini_timeouts")
                logger.warning("gemini_timeout", attempt=attempt)
                if attempt == max_retries:
                    raise LLMTimeout(settings.gemini_timeout_seconds)

            except APIError as e:
                metrics.increment("gemini_api_errors")
                logger.error("gemini_api_error", attempt=attempt, error=str(e))
                if attempt == max_retries:
                    raise InvalidAIResponse(f"Gemini API Error: {str(e)}")

            except Exception as e:
                metrics.increment("gemini_unhandled_errors")
                logger.error("gemini_unhandled_error", attempt=attempt, error=str(e))
                if attempt == max_retries:
                    raise InvalidAIResponse(f"Unhandled generation error: {str(e)}")

        raise InvalidAIResponse("Failed after max retries")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate free-form text with Gemini."""
        client = self._get_client()
        if not client:
            raise InvalidAIResponse("Gemini API key is not configured")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
            max_output_tokens=settings.gemini_max_output_tokens,
        )

        try:
            logger.info("calling_gemini_api_text", model=settings.gemini_model)
            with timer("gemini_text_duration"):
                task = client.aio.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=config,
                )
                response = await asyncio.wait_for(task, timeout=settings.gemini_timeout_seconds)
            
            if not response.text:
                raise InvalidAIResponse("Empty response from model")
            return response.text

        except asyncio.TimeoutError:
            raise LLMTimeout(settings.gemini_timeout_seconds)
        except Exception as e:
            raise InvalidAIResponse(f"Text generation failed: {str(e)}")


# Singleton client
gemini_client = GeminiClient()
