"""Results endpoints — return risk assessment and recommendations."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.core.database import get_db

router = APIRouter()


class ResultsResponse(BaseModel):
    session_id: str
    phq9_score: Optional[int]
    phq9_severity: Optional[str]
    gad7_score: Optional[int]
    gad7_severity: Optional[str]
    pss10_score: Optional[int]
    pss10_severity: Optional[str]
    rule_based_risk: Optional[str]
    ml_risk_label: Optional[str]
    ml_confidence: Optional[float]
    coping_suggestions: List[str]
    counseling_resources: Dict


@router.get("/{session_id}", response_model=ResultsResponse)
async def get_results(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get complete results for a finished screening session."""
    # TODO: Query risk_scores table
    # TODO: Generate coping suggestions based on risk domains
    return {
        "session_id": session_id,
        "phq9_score": None,
        "phq9_severity": None,
        "gad7_score": None,
        "gad7_severity": None,
        "pss10_score": None,
        "pss10_severity": None,
        "rule_based_risk": None,
        "ml_risk_label": None,
        "ml_confidence": None,
        "coping_suggestions": ["Deep breathing exercises", "Maintain regular sleep schedule"],
        "counseling_resources": {
            "name": "University Counseling Center",
            "phone": "Contact your campus helpdesk",
            "booking_url": "#",
        },
    }
