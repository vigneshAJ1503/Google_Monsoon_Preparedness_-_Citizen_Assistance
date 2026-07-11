"""
Safety Assistant endpoints.
Serves grounded safety guidelines and contextual advice.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional, List

from src.api.middleware.rate_limiter import check_rate_limit
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import HouseholdRepository
from src.application.assistant_service import assistant_service
from src.application.translation_service import translation_service
from src.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class AskQuestionRequest(BaseModel):
    question: str = Field(..., max_length=500, description="Citizen safety question")
    household_id: Optional[str] = Field(None, description="UUID of household for grounding context")


class AskQuestionResponse(BaseModel):
    answer: str
    sources: List[str]
    observed_at: Optional[str] = None
    live_data_used: bool
    is_stale: bool = False


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
    summary="Ask safety assistant a weather-aware question",
    dependencies=[Depends(check_rate_limit)],
)
async def ask_assistant(
    request: Request,
    body: AskQuestionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submit a monsoon safety question. Returns a grounded GenAI response.
    Includes details about source data age and live validation.
    Translates response if language is set to Tamil or Hindi.
    """
    # 1. Fetch household context if UUID is provided
    household = None
    if body.household_id:
        hh_repo = HouseholdRepository(db)
        try:
            household = await hh_repo.get_by_id(UUID(body.household_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid household UUID format")

    # 2. Run assistant Q&A pipeline
    res = await assistant_service.answer_question(
        question=body.question,
        household=household,
        db=db,
    )

    # 3. Handle translation if requested by user preference
    lang = household.preferred_language if household else "en"
    if lang != "en" and res.get("answer"):
        logger.info("translating_assistant_response", lang=lang)
        translated_answer = await translation_service.translate_text(res["answer"], lang)
        res["answer"] = translated_answer

    return AskQuestionResponse(
        answer=res["answer"],
        sources=res["sources"],
        observed_at=res.get("observed_at"),
        live_data_used=res["live_data_used"],
        is_stale=res.get("is_stale", False),
    )
