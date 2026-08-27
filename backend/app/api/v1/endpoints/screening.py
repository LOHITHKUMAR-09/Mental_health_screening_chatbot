"""Screening endpoints - direct questionnaire response submission and scoring."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.models.screening_response import ScreeningResponse
from app.models.session import ScreeningSession
from app.screening.scorers import PHQ9Scorer, GAD7Scorer, PSS10Scorer

router = APIRouter()

INSTRUMENT_TOTALS = {"phq9": 9, "gad7": 7, "pss10": 10}
VALID_INSTRUMENTS = set(INSTRUMENT_TOTALS.keys())


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


@router.post("/submit-item", status_code=201)
async def submit_screening_item(data: ScreeningItemSubmit, db: AsyncSession = Depends(get_db)):
    """Submit a single questionnaire item response."""
    if data.instrument not in VALID_INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unknown instrument: {data.instrument}. Use phq9, gad7, or pss10")

    # Verify session exists
    result = await db.execute(select(ScreeningSession).where(ScreeningSession.id == data.session_id))
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate response value range
    max_val = 3 if data.instrument in ("phq9", "gad7") else 4
    if not (0 <= data.response_value <= max_val):
        raise HTTPException(status_code=400, detail=f"response_value must be 0-{max_val} for {data.instrument}")

    # Upsert response (replace if already submitted)
    existing_q = await db.execute(
        select(ScreeningResponse).where(
            ScreeningResponse.session_id == data.session_id,
            ScreeningResponse.instrument == data.instrument,
            ScreeningResponse.item_number == data.item_number,
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        existing.response_value = data.response_value
    else:
        db.add(ScreeningResponse(
            session_id=data.session_id,
            instrument=data.instrument,
            item_number=data.item_number,
            response_value=data.response_value,
        ))

    return {"status": "recorded", "instrument": data.instrument, "item": data.item_number, "value": data.response_value}


@router.get("/{session_id}/score/{instrument}", response_model=ScreeningScoreResponse)
async def get_instrument_score(session_id: str, instrument: str, db: AsyncSession = Depends(get_db)):
    """Get the current score for a specific instrument in a session."""
    if instrument not in VALID_INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unknown instrument. Use: phq9, gad7, pss10")

    result = await db.execute(
        select(ScreeningResponse).where(
            ScreeningResponse.session_id == session_id,
            ScreeningResponse.instrument == instrument,
        )
    )
    rows = result.scalars().all()
    responses = {r.item_number: r.response_value for r in rows}

    # Compute score using the deterministic scorers
    if instrument == "phq9":
        scored = PHQ9Scorer.score(responses)
    elif instrument == "gad7":
        scored = GAD7Scorer.score(responses)
    else:
        scored = PSS10Scorer.score(responses)

    return ScreeningScoreResponse(
        session_id=session_id,
        instrument=instrument,
        total_score=scored.total,
        severity=scored.severity,
        items_completed=len(responses),
        items_total=INSTRUMENT_TOTALS[instrument],
    )
