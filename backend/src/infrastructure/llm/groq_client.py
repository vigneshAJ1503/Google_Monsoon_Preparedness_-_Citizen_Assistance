"""
Groq API client (OpenAI-compatible).
Free tier: 14,400 req/day for Llama 3.1 8B, 6,000 req/day for Llama 3.3 70B.
No credit card required for free tier.
"""

from typing import Type, TypeVar, Optional
import json
import asyncio
from pydantic import BaseModel
from openai import AsyncOpenAI

from src.config import settings
from src.domain.exceptions.llm import LLMTimeout, InvalidAIResponse
from src.observability.logger import get_logger
from src.observability.metrics import timer, metrics

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class GroqClient:
    """Async wrapper for Groq API (OpenAI-compatible)."""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    def _get_client(self) -> Optional[AsyncOpenAI]:
        """Lazy initialization of the Groq client."""
        if self._client is not None:
            return self._client

        if not settings.groq_api_key:
            logger.warning("groq_api_key_missing", message="Groq API requests will fallback to deterministic generation")
            return None

        try:
            self._client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            return self._client
        except Exception as e:
            logger.error("groq_client_init_failed", error=str(e))
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
        Note: Groq doesn't support native JSON schema like Gemini,
        so we use function calling / tool use approach.
        """
        client = self._get_client()
        if not client:
            raise InvalidAIResponse("Groq API key is not configured")

        # Convert Pydantic schema to JSON Schema for function calling
        schema = response_schema.model_json_schema()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "generate_response",
                    "description": "Generate structured response matching the schema",
                    "parameters": schema,
                },
            }
        ]

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "calling_groq_api",
                    model=settings.groq_model,
                    schema=response_schema.__name__,
                    attempt=attempt,
                )

                with timer("groq_generation_duration"):
                    response = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=settings.groq_model,
                            messages=messages,
                            tools=tools,
                            tool_choice={"type": "function", "function": {"name": "generate_response"}},
                            temperature=0.2,
                            max_tokens=settings.groq_max_output_tokens,
                        ),
                        timeout=settings.groq_timeout_seconds,
                    )

                metrics.increment("groq_success_rate")

                tool_calls = response.choices[0].message.tool_calls
                if tool_calls and tool_calls[0].function.arguments:
                    try:
                        parsed_data = json.loads(tool_calls[0].function.arguments)
                        validated_obj = response_schema.model_validate(parsed_data)
                        return validated_obj
                    except Exception as e:
                        logger.warning(
                            "groq_schema_validation_failed",
                            attempt=attempt,
                            error=str(e),
                            text=tool_calls[0].function.arguments,
                        )
                        metrics.increment("groq_schema_failures")
                        if attempt == max_retries:
                            raise InvalidAIResponse(f"Schema validation failed: {str(e)}", tool_calls[0].function.arguments)
                else:
                    raise InvalidAIResponse("No function call returned from model")

            except asyncio.TimeoutError:
                metrics.increment("groq_timeouts")
                logger.warning("groq_timeout", attempt=attempt)
                if attempt == max_retries:
                    raise LLMTimeout(settings.groq_timeout_seconds)

            except Exception as e:
                metrics.increment("groq_api_errors")
                logger.error("groq_api_error", attempt=attempt, error=str(e))
                if attempt == max_retries:
                    raise InvalidAIResponse(f"Groq API Error: {str(e)}")

        raise InvalidAIResponse("Failed after max retries")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate free-form text with Groq."""
        client = self._get_client()
        if not client:
            raise InvalidAIResponse("Groq API key is not configured")

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
                raise InvalidAIResponse("Empty response from model")
            return response.choices[0].message.content

        except asyncio.TimeoutError:
            raise LLMTimeout(settings.groq_timeout_seconds)
        except Exception as e:
            raise InvalidAIResponse(f"Text generation failed: {str(e)}")


# Singleton client
groq_client = GroqClient()