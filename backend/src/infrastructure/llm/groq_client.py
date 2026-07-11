"""Groq API client (OpenAI-compatible).
Free tier: 14,400 req/day for Llama 3.1 8B, 6,000 req/day for Llama 3.3 70B.
No credit card required for free tier.
"""

import asyncio
import json
import re
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.config import settings
from src.domain.exceptions.llm import InvalidAIResponse, LLMTimeout
from src.observability.logger import get_logger
from src.observability.metrics import metrics, timer

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class GroqClient:
    """Async wrapper for Groq API (OpenAI-compatible)."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI | None:
        """Lazy initialization of the Groq client."""
        if self._client is not None:
            return self._client

        if not settings.groq_api_key:
            logger.warning(
                "groq_api_key_missing",
                message="Groq API requests will fallback to deterministic generation",
            )
            return None

        try:
            self._client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            return self._client
        except Exception as e:
            logger.exception("groq_client_init_failed", error=str(e))
            return None

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        max_retries: int = 1,
    ) -> T:
        """Generate structured output adhering to a Pydantic schema.
        Uses text generation with JSON parsing instead of function calling
        for better compatibility with Groq models.
        """
        client = self._get_client()
        if not client:
            msg = "Groq API key is not configured"
            raise InvalidAIResponse(msg)

        # Build JSON schema from Pydantic model
        schema = response_schema.model_json_schema()

        # Build prompt with JSON schema instruction
        json_schema_str = json.dumps(schema, indent=2)
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        messages.append({
            "role": "user", 
            "content": (
                f"{prompt}\n\n"
                f"Respond with valid JSON matching this schema:\n{json_schema_str}\n"
                f"Return only the JSON object, no additional text."
            )
        })

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "calling_groq_api_structured",
                    model=settings.groq_model,
                    schema=response_schema.__name__,
                    attempt=attempt,
                )

                with timer("groq_generation_duration"):
                    response = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=settings.groq_model,
                            messages=[
                                {"role": "system", "content": system_instruction} if system_instruction else None,
                                {"role": "user", "content": (
                                    f"{prompt}\n\n"
                                    f"Respond with valid JSON matching this schema:\n{json_schema_str}\n"
                                    f"Return only the JSON object, no additional text."
                                )}
                            ] if system_instruction else [
                                {"role": "user", "content": (
                                    f"{prompt}\n\n"
                                    f"Respond with valid JSON matching this schema:\n{json_schema_str}\n"
                                    f"Return only the JSON object, no additional text."
                                )}
                            ],
                            temperature=0.2,
                            max_tokens=settings.groq_max_output_tokens,
                            response_format={"type": "json_object"},
                        ),
                        timeout=settings.groq_timeout_seconds,
                    )

                metrics.increment("groq_success_rate")

                content = response.choices[0].message.content
                if not content:
                    raise InvalidAIResponse("Empty response from model")

                # Parse JSON from response
                try:
                    # Extract JSON from response (handle potential markdown code blocks)
                    json_str = self._extract_json(content)
                    parsed_data = json.loads(json_str)
                    return response_schema.model_validate(parsed_data)
                except Exception as e:
                    logger.warning(
                        "groq_schema_validation_failed",
                        attempt=attempt,
                        error=str(e),
                        content=content[:500],
                    )
                    metrics.increment("groq_schema_failures")
                    if attempt == max_retries:
                        msg = f"Schema validation failed: {e!s}"
                        raise InvalidAIResponse(msg, content)

            except asyncio.TimeoutError:
                metrics.increment("groq_timeouts")
                logger.warning("groq_timeout", attempt=attempt)
                if attempt == max_retries:
                    raise LLMTimeout(settings.groq_timeout_seconds)

            except Exception as e:
                metrics.increment("groq_api_errors")
                logger.exception("groq_api_error", attempt=attempt, error=str(e))
                if attempt == max_retries:
                    msg = f"Groq API Error: {e!s}"
                    raise InvalidAIResponse(msg)

        msg = "Failed after max retries"
        raise InvalidAIResponse(msg)

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        # Try to find JSON in markdown code blocks
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        
        # Try to find JSON object directly
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return text

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """Generate free-form text with Groq."""
        client = self._get_client()
        if not client:
            msg = "Groq API key is not configured"
            raise InvalidAIResponse(msg)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.info("calling_groq_api_text", model=settings.groq_model)
            with timer("groq_text_duration"):
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=settings.groq_model,
                        messages=messages,
                        temperature=0.4,
                        max_tokens=settings.groq_max_output_tokens,
                    ),
                    timeout=settings.groq_timeout_seconds,
                )

            if not response.choices[0].message.content:
                msg = "Empty response from model"
                raise InvalidAIResponse(msg)
            return response.choices[0].message.content

        except asyncio.TimeoutError:
            raise LLMTimeout(settings.groq_timeout_seconds)
        except Exception as e:
            msg = f"Text generation failed: {e!s}"
            raise InvalidAIResponse(msg)


# Singleton client
groq_client = GroqClient()
