"""Session management endpoints with conversation history retrieval."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.session import ScreeningSession
from app.models.message import ChatMessage
from app.models.user import User
from app.models.risk_score import RiskScore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_user_id_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    return payload.get("sub") if payload else None


class SessionStartResponse(BaseModel):
    session_id: str
    current_state: str
    message: str
    # Cooldown fields — present when a recent session exists
    questionnaire_blocked: bool = False
    cooldown_remaining_hours: Optional[float] = None
    previous_results: Optional[Dict[str, Any]] = None
    previous_session_id: Optional[str] = None


class SessionStateResponse(BaseModel):
    session_id: str
    current_state: str
    is_complete: bool
    started_at: str
    session_number: int


class MessageItem(BaseModel):
    id: str
    sender: str
    content: str
    state: str
    created_at: str


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id_from_token),
):
    """Start a new screening session, with cooldown check.

    If the user completed a screening within QUESTIONNAIRE_COOLDOWN_HOURS,
    questionnaire_blocked=True is returned along with the previous results so the
    frontend can skip the questionnaire and instead deliver suggestions in chat.
    """
    if not user_id:
        user = User(role="student", is_anonymous=True)
        db.add(user)
        await db.flush()
        user_id = str(user.id)

    # ── Cooldown check ────────────────────────────────────────────────
    cooldown_hours = settings.QUESTIONNAIRE_COOLDOWN_HOURS
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)

    last_session_result = await db.execute(
        select(ScreeningSession)
        .where(
            ScreeningSession.user_id == user_id,
            ScreeningSession.is_complete == True,  # noqa: E712
        )
        .order_by(desc(ScreeningSession.started_at))
        .limit(1)
    )
    last_session = last_session_result.scalar_one_or_none()

    questionnaire_blocked = False
    cooldown_remaining_hours = None
    previous_results: Optional[Dict[str, Any]] = None
    previous_session_id = None

    if last_session and last_session.started_at:
        last_started = last_session.started_at
        if last_started.tzinfo is None:
            last_started = last_started.replace(tzinfo=timezone.utc)

        if last_started > cutoff_time:
            questionnaire_blocked = True
            elapsed = (datetime.now(timezone.utc) - last_started).total_seconds() / 3600
            cooldown_remaining_hours = round(cooldown_hours - elapsed, 1)
            previous_session_id = str(last_session.id)

            risk_result = await db.execute(
                select(RiskScore).where(RiskScore.session_id == last_session.id)
            )
            risk_row = risk_result.scalar_one_or_none()
            if risk_row:
                previous_results = {
                    "session_id": str(last_session.id),
                    "phq9_score": risk_row.phq9_score,
                    "phq9_severity": risk_row.phq9_severity,
                    "gad7_score": risk_row.gad7_score,
                    "gad7_severity": risk_row.gad7_severity,
                    "pss10_score": risk_row.pss10_score,
                    "pss10_severity": risk_row.pss10_severity,
                    "rule_based_risk": risk_row.rule_based_risk,
                    "ml_risk_label": risk_row.ml_risk_label,
                    "ml_confidence": risk_row.ml_confidence,
                    "completed_at": last_session.started_at.isoformat(),
                }

    # ── Create new session ────────────────────────────────────────────
    count_result = await db.execute(
        select(func.count()).where(ScreeningSession.user_id == user_id)
    )
    session_count = count_result.scalar() or 0

    # Blocked sessions start in "cooldown" state — the state machine will
    # treat this as a conversational-only session (no questionnaire).
    initial_state = "cooldown" if questionnaire_blocked else "greeting"

    new_session = ScreeningSession(
        user_id=user_id,
        current_state=initial_state,
        session_number=session_count + 1,
    )
    db.add(new_session)
    await db.flush()

    return SessionStartResponse(
        session_id=str(new_session.id),
        current_state=initial_state,
        message="Session started. MindEase is ready.",
        questionnaire_blocked=questionnaire_blocked,
        cooldown_remaining_hours=cooldown_remaining_hours,
        previous_results=previous_results,
        previous_session_id=previous_session_id,
    )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get current state of a session."""
    result = await db.execute(select(ScreeningSession).where(ScreeningSession.id == session_id))
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionStateResponse(
        session_id=str(sess.id),
        current_state=sess.current_state,
        is_complete=sess.is_complete,
        started_at=sess.started_at.isoformat(),
        session_number=sess.session_number,
    )


@router.get("/{session_id}/messages", response_model=List[MessageItem])
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch persistent chat message history for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        MessageItem(
            id=str(m.id),
            sender=m.sender,
            content=m.content,
            state=m.state,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.post("/{session_id}/complete")
async def complete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Mark session as complete."""
    result = await db.execute(select(ScreeningSession).where(ScreeningSession.id == session_id))
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    sess.is_complete = True
    sess.ended_at = datetime.now(timezone.utc)
    return {"session_id": session_id, "status": "completed"}
