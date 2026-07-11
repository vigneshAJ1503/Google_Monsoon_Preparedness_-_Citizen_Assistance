"""Checklist endpoints.

Allows retrieving, generating, and updating emergency checklists.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.rate_limiter import check_rate_limit
from src.application.checklist_service import checklist_service
from src.application.translation_service import translation_service
from src.domain.models.checklist import Checklist, ChecklistItem, ChecklistStatus
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import HouseholdRepository
from src.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class UpdateStatusRequest(BaseModel):
    """Request body for updating checklist item status."""

    household_id: str
    item_id: str
    status: ChecklistStatus


@router.get(
    "",
    summary="Get or generate emergency checklist for household",
    dependencies=[Depends(check_rate_limit)],
)
async def get_checklist(
    _request: Request,
    household_id: Annotated[str, Query(description="UUID of the household")],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Checklist:
    """Retrieve or generate context-aware checklist items for a household.

    Translates titles and descriptions based on household preference.
    """
    # 1. Fetch household profile
    hh_repo = HouseholdRepository(db)
    try:
        household = await hh_repo.get_by_id(UUID(household_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid household UUID format")

    if not household:
        raise HTTPException(status_code=404, detail="Household profile not found")

    # 2. Fetch checklist
    checklist = await checklist_service.get_or_create_checklist(household, db)

    # 3. Translate dynamic checklist titles if preferred language is not English
    lang = household.preferred_language
    if lang != "en":
        logger.info("translating_checklist", lang=lang)
        for item in checklist.items:
            item.title = await translation_service.translate_text(item.title, lang)
            if item.description:
                item.description = await translation_service.translate_text(
                    item.description, lang,
                )
            if item.weather_context:
                item.weather_context = await translation_service.translate_text(
                    item.weather_context, lang,
                )

    return checklist


@router.post(
    "/item",
    summary="Update checklist item status",
    dependencies=[Depends(check_rate_limit)],
)
async def update_item_status(
    _request: Request,
    body: UpdateStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChecklistItem:
    """Update status of a checklist item (pending, completed, not_applicable)."""
    try:
        return await checklist_service.update_item_status(
            body.household_id, body.item_id, body.status, db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update item status")
