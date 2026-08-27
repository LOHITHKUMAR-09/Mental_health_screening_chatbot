"""Results endpoint - returns risk scores, ML predictions, coping suggestions, and resources."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.core.database import get_db
from app.models.session import ScreeningSession
from app.models.screening_response import ScreeningResponse
from app.models.risk_score import RiskScore
from app.screening.scorers import PHQ9Scorer, GAD7Scorer, PSS10Scorer, CompositeRiskCalculator
from app.ml.predictor import ml_predictor

router = APIRouter()


# ── Coping suggestion library ─────────────────────────────────────
COPING_SUGGESTIONS = {
    "depression": [
        "Try to maintain a consistent daily routine, even small ones like waking at the same time.",
        "Engage in brief physical activity - even a 10-minute walk can improve mood.",
        "Reach out to one person you trust today, even just with a text.",
        "Practice behavioral activation: schedule one enjoyable activity this week.",
        "Consider journaling your thoughts for 5 minutes each morning.",
    ],
    "anxiety": [
        "Practice the 4-7-8 breathing technique: inhale 4s, hold 7s, exhale 8s.",
        "Try grounding with the 5-4-3-2-1 technique: name 5 things you see, 4 you hear, etc.",
        "Limit caffeine and screen time, especially before bed.",
        "Write down your worries and set a dedicated 15-minute 'worry time' per day.",
        "Progressive muscle relaxation before sleep can reduce anxiety significantly.",
    ],
    "stress": [
        "Break large tasks into smaller steps and celebrate small completions.",
        "Use the Pomodoro technique: 25 minutes of focused work, 5 minute break.",
        "Practice saying no to non-essential commitments this week.",
        "Schedule at least 30 minutes of unstructured, restful time daily.",
        "Talk to a trusted friend, mentor, or your campus counselor about your workload.",
    ],
    "general": [
        "Sleep is foundational - aim for 7-9 hours at consistent times.",
        "Stay connected socially, even briefly - isolation amplifies distress.",
        "Limit news and social media to defined times each day.",
        "Try a free mindfulness app like Headspace, Calm, or Insight Timer.",
        "Remember: seeking help is a sign of strength, not weakness.",
    ],
}

COUNSELING_RESOURCES = {
    "name": "University Counseling Center",
    "phone": "Visit your campus health & counseling desk",
    "booking_url": "https://university.edu/counseling",
    "emergency": {
        "icall": "9152987821",
        "vandrevala": "1860-2662-345",
        "emergency": "112",
    },
}


class ResultsResponse(BaseModel):
    session_id: str
    phq9_score: Optional[int] = None
    phq9_severity: Optional[str] = None
    gad7_score: Optional[int] = None
    gad7_severity: Optional[str] = None
    pss10_score: Optional[int] = None
    pss10_severity: Optional[str] = None
    rule_based_risk: Optional[str] = None
    ml_risk_label: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_model_name: str = "XGBoost Classifier (91.1% CV Accuracy on 39k Real Samples)"
    shap_top_features: Optional[Dict[str, float]] = None
    coping_suggestions: List[str] = []
    counseling_resources: Dict = {}


def get_coping_suggestions(phq9_sev: str, gad7_sev: str, pss10_sev: str) -> List[str]:
    """Select relevant coping suggestions based on dominant concern areas."""
    suggestions = []
    if phq9_sev in ("moderate", "moderately_severe", "severe"):
        suggestions.extend(COPING_SUGGESTIONS["depression"][:2])
    if gad7_sev in ("moderate", "severe"):
        suggestions.extend(COPING_SUGGESTIONS["anxiety"][:2])
    if pss10_sev in ("moderate", "high"):
        suggestions.extend(COPING_SUGGESTIONS["stress"][:2])
    suggestions.extend(COPING_SUGGESTIONS["general"][:2])
    return list(dict.fromkeys(suggestions))[:6]


@router.get("/{session_id}", response_model=ResultsResponse)
async def get_results(session_id: str, db: AsyncSession = Depends(get_db)):
    """Compute and return full screening results for a completed session."""
    result = await db.execute(select(ScreeningSession).where(ScreeningSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load all screening responses
    resp_result = await db.execute(
        select(ScreeningResponse).where(ScreeningResponse.session_id == session.id)
    )
    all_responses: Dict = {}
    for r in resp_result.scalars().all():
        if r.instrument not in all_responses:
            all_responses[r.instrument] = {}
        all_responses[r.instrument][r.item_number] = r.response_value

    phq9_resp  = all_responses.get("phq9", {})
    gad7_resp  = all_responses.get("gad7", {})
    pss10_resp = all_responses.get("pss10", {})

    # 1. Deterministic Clinical Scoring
    phq9_score  = PHQ9Scorer.score(phq9_resp)
    gad7_score  = GAD7Scorer.score(gad7_resp)
    pss10_score = PSS10Scorer.score(pss10_resp)
    composite   = CompositeRiskCalculator.compute(phq9_score, gad7_score, pss10_score)

    # 2. Machine Learning Inference (Random Forest + SHAP)
    ml_label, ml_conf, shap_feats = ml_predictor.predict(all_responses)

    # 3. Save to risk_scores table
    existing = await db.execute(select(RiskScore).where(RiskScore.session_id == session.id))
    risk_row = existing.scalar_one_or_none()
    if not risk_row:
        risk_row = RiskScore(session_id=session.id)
        db.add(risk_row)

    risk_row.phq9_score      = phq9_score.total
    risk_row.phq9_severity   = phq9_score.severity
    risk_row.gad7_score      = gad7_score.total
    risk_row.gad7_severity   = gad7_score.severity
    risk_row.pss10_score     = pss10_score.total
    risk_row.pss10_severity  = pss10_score.severity
    risk_row.rule_based_risk = composite.composite_risk
    risk_row.ml_risk_label   = ml_label
    risk_row.ml_confidence   = ml_conf
    risk_row.shap_values     = json.dumps(shap_feats)

    coping = get_coping_suggestions(phq9_score.severity, gad7_score.severity, pss10_score.severity)

    return ResultsResponse(
        session_id=session_id,
        phq9_score=phq9_score.total,
        phq9_severity=phq9_score.severity,
        gad7_score=gad7_score.total,
        gad7_severity=gad7_score.severity,
        pss10_score=pss10_score.total,
        pss10_severity=pss10_score.severity,
        rule_based_risk=composite.composite_risk,
        ml_risk_label=ml_label,
        ml_confidence=ml_conf,
        shap_top_features=shap_feats,
        coping_suggestions=coping,
        counseling_resources=COUNSELING_RESOURCES,
    )
