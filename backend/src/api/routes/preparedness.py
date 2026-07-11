"""
Preparedness Plan endpoints.
Accepts household profiles and generates/caches plans.
Supports translations.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.api.middleware.rate_limiter import check_rate_limit
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import HouseholdRepository
from src.domain.models.household import HouseholdProfile
from src.domain.models.preparedness import PreparednessePlan
from src.application.preparedness_service import preparedness_service
from src.application.translation_service import translation_service
from src.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/plan",
    response_model=PreparednessePlan,
    summary="Generate personalized monsoon preparedness plan",
    dependencies=[Depends(check_rate_limit)],
)
async def generate_preparedness_plan(
    request: Request,
    profile: HouseholdProfile,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Generate, cache and return a customized preparedness plan.
    Saves/updates the household profile in the database.
    Translates the response if language is set to Tamil or Hindi.
    """
    # 1. Persist household profile first
    household_repo = HouseholdRepository(db)
    saved_profile = await household_repo.save(profile)
    
    # Update profile ID in our working object
    profile.id = saved_profile.id

    # 2. Generate plan
    plan = await preparedness_service.generate_plan(profile, db, bypass_cache=False)

    # 3. Handle Translations if requested
    lang = profile.preferred_language
    if lang != "en":
        logger.info("translating_plan", lang=lang)
        
        # Translate risk summary reasons
        translated_reasons = []
        for reason in plan.risk_summary.reasons:
            translated_reasons.append(
                await translation_service.translate_text(reason, lang)
            )
        plan.risk_summary.reasons = translated_reasons

        # Translate actions
        for action in plan.actions_immediate:
            action.action = await translation_service.translate_text(action.action, lang)
            if action.category:
                action.category = await translation_service.translate_text(action.category, lang)
                
        for action in plan.actions_next_6_hours:
            action.action = await translation_service.translate_text(action.action, lang)
            if action.category:
                action.category = await translation_service.translate_text(action.category, lang)
                
        for action in plan.actions_next_24_hours:
            action.action = await translation_service.translate_text(action.action, lang)
            if action.category:
                action.category = await translation_service.translate_text(action.category, lang)

        for action in plan.household_specific_actions:
            action.action = await translation_service.translate_text(action.action, lang)
            if action.category:
                action.category = await translation_service.translate_text(action.category, lang)

        # Translate kit items
        translated_kit = []
        for item in plan.emergency_kit:
            translated_kit.append(
                await translation_service.translate_text(item, lang)
            )
        plan.emergency_kit = translated_kit

        # Translate limitations
        translated_lims = []
        for lim in plan.limitations:
            translated_lims.append(
                await translation_service.translate_text(lim, lang)
            )
        plan.limitations = translated_lims

    return plan
