"""
Preparedness Service.
Generates personalized preparedness plans using weather, risk, and Gemini AI.
Includes a robust deterministic fallback plan generator if LLM is unavailable or fails.
"""

from datetime import datetime, timezone
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.household import HouseholdProfile, HousingType
from src.domain.models.preparedness import PreparednessePlan, RiskSummary, ActionItem
from src.domain.rules.risk_classifier import classify_risk
from src.application.weather_service import weather_service
from src.infrastructure.llm.gemini_client import gemini_client
from src.infrastructure.llm.prompt_templates import SYSTEM_SAFETY_POLICY, PREPAREDNESS_PLAN_PROMPT
from src.infrastructure.llm.context_builder import build_preparedness_plan_prompt_vars
from src.infrastructure.persistence.repositories import PreparednessPlanRepository, AlertRepository
from src.observability.logger import get_logger

logger = get_logger(__name__)


class PreparednessService:
    """Manages the creation and retrieval of personalized preparedness plans."""

    async def generate_plan(
        self, household: HouseholdProfile, db: AsyncSession, bypass_cache: bool = False
    ) -> PreparednessePlan:
        """
        Generate a personalized preparedness plan.
        Steps:
        1. Fetch weather context
        2. Classify risk level deterministically
        3. Fetch active alerts
        4. Attempt Gemini LLM generation with schema
        5. Fallback to local deterministic rules if Gemini fails/not configured
        """
        household_id = UUID(household.id) if household.id else None
        repo = PreparednessPlanRepository(db)

        # Try cache first if not bypass
        if household_id and not bypass_cache:
            cached = await repo.get_by_household(household_id)
            if cached:
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                # Parse timezone safely
                expires = cached.expires_at.replace(tzinfo=timezone.utc) if cached.expires_at else None
                if not expires or expires > now:
                    logger.info("plan_cache_hit", household_id=str(household_id))
                    return PreparednessePlan(**cached.plan_data)

        # 1. Weather
        weather = await weather_service.get_weather_context(
            household.location_lat, household.location_lng
        )

        # 2. Risk Classification
        risk_summary = classify_risk(weather, household)

        # 3. Active Alerts
        alert_repo = AlertRepository(db)
        active_alerts = await alert_repo.get_active_alerts()
        # Filter alerts that match household location roughly (same district/approx grid)
        # For simplicity, we filter in code
        matched_alerts = []
        for a in active_alerts:
            if a.location_lat is not None and a.location_lng is not None:
                # ~10km grid matching
                if (
                    abs(a.location_lat - household.location_lat) < 0.1
                    and abs(a.location_lng - household.location_lng) < 0.1
                ):
                    matched_alerts.append(a)

        # Check if LLM is available
        llm_ready = gemini_client._get_client() is not None

        plan = None
        if llm_ready:
            try:
                # 4. Gemini structured generation
                prompt_vars = build_preparedness_plan_prompt_vars(
                    weather, household, risk_summary.level.value, risk_summary.reasons, matched_alerts
                )
                prompt = PREPAREDNESS_PLAN_PROMPT.format(**prompt_vars)

                plan = await gemini_client.generate_structured(
                    prompt=prompt,
                    response_schema=PreparednessePlan,
                    system_instruction=SYSTEM_SAFETY_POLICY,
                )
                
                # Tag generation metadata
                plan.generated_at = datetime.utcnow().isoformat()
                plan.data_sources = ["Open-Meteo", "NDMA Alerts", "Google Gemini AI"]
                logger.info("plan_generated_via_llm", household_id=str(household_id))
            except Exception as e:
                logger.error("llm_plan_generation_failed_falling_back", error=str(e))

        # 5. Deterministic fallback plan if Gemini is disabled or fails
        if plan is None:
            plan = self._generate_deterministic_fallback_plan(
                weather, household, risk_summary, matched_alerts
            )
            logger.info("plan_generated_via_deterministic_fallback", household_id=str(household_id))

        # Cache plan
        if household_id:
            await repo.save(
                household_id=household_id,
                plan_data=plan.model_dump(mode='json'),
                weather_context=weather.model_dump(mode='json'),
                risk_level=risk_summary.level.value,
                ttl_hours=1,
            )

        return plan

    def _generate_deterministic_fallback_plan(
        self,
        weather: any,
        household: HouseholdProfile,
        risk_summary: RiskSummary,
        alerts: list,
    ) -> PreparednessePlan:
        """Create a complete rules-based plan when LLM is unavailable."""
        immediate = []
        next_6 = []
        next_24 = []
        hh_specific = []
        kit = [
            "Drinking water (4 liters per person per day)",
            "Non-perishable food (biscuits, parched rice)",
            "First aid kit and personal medicines",
            "Flashlight with extra batteries",
            "Fully charged power bank",
            "Important documents in waterproof folder",
        ]

        # Common rules
        immediate.append(
            ActionItem(action="Charge all mobile phones and emergency lanterns immediately.", priority=5, category="safety")
        )
        next_6.append(
            ActionItem(action="Store drinking water in clean containers.", priority=4, category="supplies")
        )

        # Weather-based actions
        if weather.current.rainfall.forecast_mm >= 50.0:
            immediate.append(
                ActionItem(action="Move valuable electronic appliances off the floor.", priority=5, category="property")
            )
            next_24.append(
                ActionItem(action="Ensure vehicle is parked on elevated ground away from trees.", priority=4, category="property")
            )

        if weather.current.wind.speed_kmph >= 50.0:
            immediate.append(
                ActionItem(action="Close and secure all doors and windows.", priority=5, category="property")
            )

        # Vulnerability-based actions
        if household.has_children:
            hh_specific.append(
                ActionItem(action="Keep children indoors. Prepare baby formula and snacks.", priority=5, category="safety")
            )
            kit.append("Baby food, milk powder, and extra diapers")

        if household.has_elderly:
            hh_specific.append(
                ActionItem(action="Check prescriptions and keep elderly mobility aids accessible.", priority=5, category="medical")
            )
            kit.append("Elderly medicines list and essential prescription files")

        if household.has_pets:
            hh_specific.append(
                ActionItem(action="Bring pets indoors. Prepare a collar and leash.", priority=4, category="safety")
            )
            kit.append("Pet food and clean water supply")

        if household.housing_type in (HousingType.KUTCHA_HOUSE, HousingType.SLUM):
            immediate.append(
                ActionItem(
                    action="Vulnerable structure: Identify and prepare to evacuate to the nearest official concrete shelter.",
                    priority=5,
                    category="evacuation",
                )
            )

        # Active alert actions
        for a in alerts:
            immediate.append(
                ActionItem(action=f"ALERT RULE: {a.description}", priority=5, category="safety")
            )

        return PreparednessePlan(
            risk_summary=risk_summary,
            actions_immediate=immediate,
            actions_next_6_hours=next_6,
            actions_next_24_hours=next_24,
            emergency_kit=kit,
            household_specific_actions=hh_specific,
            limitations=[
                "AI generation unavailable. Plan generated using static safety rules.",
                "Real-time road closures or specific shelter locations are not verified.",
            ],
            weather_context_summary=(
                f"Location: {household.location_name or 'N/A'}. "
                f"Rainfall expected: {weather.current.rainfall.forecast_mm:.1f}mm."
            ),
            generated_at=datetime.utcnow().isoformat(),
            data_sources=["Deterministic Rule Engine", "Local Safety Standards"],
        )


# Singleton
preparedness_service = PreparednessService()
