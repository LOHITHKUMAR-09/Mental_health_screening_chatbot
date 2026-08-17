"""Screening endpoints — direct questionnaire response submission."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.core.database import get_db

router = APIRouter()


class ScreeningItemSubmit(BaseModel):
    session_id: str
    instrument: str  # phq9 | gad7 | pss10
    item_number: int
    response_value: int


class ScreeningScoreResponse(BaseModel):
    session_id: str
    instrument: str
    total_score: int
    severity: str
    items_completed: int
    items_total: int


@router.post("/submit-item")
async def submit_screening_item(data: ScreeningItemSubmit, db: AsyncSession = Depends(get_db)):
    """Submit a single questionnaire item response."""
    # TODO: Validate response value range for instrument
    # TODO: Store in screening_responses table
    return {"status": "recorded", "instrument": data.instrument, "item": data.item_number}


@router.get("/{session_id}/score/{instrument}", response_model=ScreeningScoreResponse)
async def get_instrument_score(session_id: str, instrument: str, db: AsyncSession = Depends(get_db)):
    """Get the current score for a specific instrument in a session."""
    # TODO: Query responses, run deterministic scorer
    return {
        "session_id": session_id,
        "instrument": instrument,
        "total_score": 0,
        "severity": "minimal",
        "items_completed": 0,
        "items_total": 9 if instrument == "phq9" else 7 if instrument == "gad7" else 10,
    }
