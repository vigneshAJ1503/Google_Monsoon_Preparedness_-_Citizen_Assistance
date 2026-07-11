"""
Checklist endpoints.
Allows retrieving, generating, and updating emergency checklists.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel

from src.api.middleware.rate_limiter import check_rate_limit
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import HouseholdRepository
from src.domain.models.checklist import Checklist, ChecklistItem, ChecklistStatus
from src.application.checklist_service import checklist_service
from src.application.translation_service import translation_service
from src.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class UpdateStatusRequest(BaseModel):
    household_id: str
    item_id: str
    status: ChecklistStatus


@router.get(
    "",
    response_model=Checklist,
    summary="Get or generate emergency checklist for household",
    dependencies=[Depends(check_rate_limit)],
)
async def get_checklist(
    request: Request,
    household_id: str = Query(..., description="UUID of the household"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve or generate context-aware checklist items for a household.
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
                item.description = await translation_service.translate_text(item.description, lang)
            if item.weather_context:
                item.weather_context = await translation_service.translate_text(item.weather_context, lang)

    return checklist


@router.post(
    "/item",
    response_model=ChecklistItem,
    summary="Update checklist item status",
    dependencies=[Depends(check_rate_limit)],
)
async def update_item_status(
    request: Request,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update status of a checklist item (pending, completed, not_applicable).
    """
    try:
        updated = await checklist_service.update_item_status(
            body.household_id, body.item_id, body.status, db
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update item status")
