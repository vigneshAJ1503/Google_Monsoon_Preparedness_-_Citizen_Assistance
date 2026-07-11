"""Safety Assistant Service.
Implements a complete RAG (Retrieval-Augmented Generation) pipeline.
Steps: Input validation -> retrieval -> safety checks -> generation -> verification.
"""

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.weather_service import weather_service
from src.domain.models.alert import Alert
from src.domain.models.household import HouseholdProfile
from src.domain.models.weather import WeatherContext
from src.infrastructure.knowledge.safety_knowledge import get_relevant_guidelines
from src.infrastructure.llm.context_builder import build_assistant_qna_prompt_vars
from src.infrastructure.llm.groq_client import groq_client
from src.infrastructure.llm.output_validator import clean_and_validate_response
from src.infrastructure.llm.prompt_templates import (
    ASSISTANT_QNA_PROMPT,
    SYSTEM_SAFETY_POLICY,
)
from src.infrastructure.persistence.repositories import AlertRepository
from src.observability.logger import get_logger

logger = get_logger(__name__)


class AssistantService:
    """Orchestrates the safety Q&A assistant pipeline."""

    async def answer_question(
        self,
        question: str,
        household: HouseholdProfile | None,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Execute RAG flow for a user safety query."""
        # 1. Input validation & Sanitization (prevent injection)
        cleaned_question = self._sanitize_input(question)
        if not cleaned_question:
            return {
                "answer": "Please ask a valid safety question regarding monsoons.",
                "sources": [],
                "live_data_used": False,
            }

        # Determine location coordinates (default to Coimbatore if no household)
        lat = household.location_lat if household else 11.0168
        lng = household.location_lng if household else 76.9558

        # 2. Fetch Live Context
        weather = await weather_service.get_weather_context(lat, lng)

        # Fetch Alerts
        alert_repo = AlertRepository(db)
        alerts = await alert_repo.get_active_alerts()
        # Filter alerts that match household location roughly (same district/approx grid)
        matched_alerts = []
        for a in alerts:
            if a.location_lat is not None and a.location_lng is not None:
                if abs(a.location_lat - lat) < 0.1 and abs(a.location_lng - lng) < 0.1:
                    matched_alerts.append(a)

        # 3. Retrieve Safety Knowledge (RAG)
        knowledge = get_relevant_guidelines(cleaned_question)

        # Build prompt vars
        prompt_vars = build_assistant_qna_prompt_vars(
            weather=weather,
            household=household,
            active_alerts=matched_alerts,
            trusted_knowledge=knowledge,
            user_question=cleaned_question,
        )

        prompt = ASSISTANT_QNA_PROMPT.format(**prompt_vars)

        # Determine if Groq client is active
        llm_ready = groq_client._get_client() is not None

        sources = ["National Disaster Management Guidelines (NDMA India)"]
        if weather.data_available:
            sources.append("Open-Meteo Weather API")
        if matched_alerts:
            sources.append("NDMA / SACHET Disaster Alerts")

        if llm_ready:
            try:
                # 4. LLM Generation
                raw_response = await groq_client.generate_text(
                    prompt=prompt,
                    system_instruction=SYSTEM_SAFETY_POLICY,
                )

                # 5. Output Validation (Verify no unverified claims or fake dates)
                answer = clean_and_validate_response(raw_response)
                logger.info("assistant_responded_via_llm")

                return {
                    "answer": answer,
                    "sources": sources,
                    "observed_at": weather.current.observed_at.isoformat(),
                    "live_data_used": weather.data_available,
                    "is_stale": weather.current.is_stale,
                }
            except Exception as e:
                logger.exception("assistant_generation_failed_falling_back", error=str(e))

        # 6. Fallback answers if LLM fails or is disabled
        answer = self._generate_fallback_answer(
            cleaned_question, weather, matched_alerts,
        )
        logger.info("assistant_responded_via_fallback")

        return {
            "answer": answer,
            "sources": ["Local safety knowledge templates"],
            "observed_at": weather.current.observed_at.isoformat(),
            "live_data_used": False,
        }

    def _sanitize_input(self, text: str) -> str:
        """Sanitize query string to block prompt injection patterns."""
        # Remove markdown/HTML tags and command sequences
        clean = re.sub(r"<[^>]*>", "", text)
        clean = re.sub(r"[{}\[\]]", "", clean)
        # Check for system instructions override attempts
        if any(
            keyword in clean.lower()
            for keyword in [
                "ignore previous",
                "system prompt",
                "override instructions",
                "you must now",
            ]
        ):
            logger.warning("potential_prompt_injection_blocked", input=text)
            return ""
        return clean.strip()[
            :300
        ]  # Limit length to 300 characters to prevent buffer issues

    def _generate_fallback_answer(
        self, query: str, weather: WeatherContext, alerts: list[Alert],
    ) -> str:
        """Generate a basic templates response based on user keywords."""
        query_lower = query.lower()

        if any(w in query_lower for w in ["prepare", "checklist", "kit", "plan"]):
            return (
                "To prepare for monsoons, please complete your personalized checklist and store at least 3 days of clean drinking water, "
                "non-perishable food, flashlights, and a first-aid kit. Charge all power banks and keep personal documents in a waterproof bag."
            )

        if any(w in query_lower for w in ["flood", "water", "drain"]):
            return (
                "In case of flooding, immediately turn off the main electricity switch in your home. Do not wade, walk, or drive through "
                "moving water. Move children and elderly family members to higher floors and stay tuned to official alerts."
            )

        if any(w in query_lower for w in ["lightning", "thunder", "storm"]):
            return (
                "During a thunderstorm, stay indoors and keep away from electrical appliances, metal objects, and water taps. "
                "Unplug sensitive electronics and avoid using wired phones."
            )

        # Default fallback with weather context
        rain_info = (
            f"Current rainfall forecast: {weather.current.rainfall.forecast_mm:.1f}mm."
        )
        return (
            f"For personalized monsoon safety guidance, please use the Preparedness Plan or Checklist features. "
            f"{rain_info} Stay alert and follow official NDMA advisories."
        )


# Singleton
assistant_service = AssistantService()
