"""Session management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.session import Session
from app.models.user import User
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


class SessionStateResponse(BaseModel):
    session_id: str
    current_state: str
    is_complete: bool
    started_at: str
    session_number: int


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id_from_token),
):
    """Start a new screening session."""
    if not user_id:
        # Create anon user on the fly
        user = User(role="student", is_anonymous=True)
        db.add(user)
        await db.flush()
        user_id = str(user.id)

    # Count existing sessions for this user
    count_result = await db.execute(
        select(func.count()).where(Session.user_id == user_id)
    )
    session_count = count_result.scalar() or 0

    session = Session(
        user_id=user_id,
        current_state="greeting",
        session_number=session_count + 1,
    )
    db.add(session)
    await db.flush()

    return SessionStartResponse(
        session_id=str(session.id),
        current_state="greeting",
        message="Session started. MindEase is ready.",
    )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get current state of a session."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionStateResponse(
        session_id=str(session.id),
        current_state=session.current_state,
        is_complete=session.is_complete,
        started_at=session.started_at.isoformat(),
        session_number=session.session_number,
    )


@router.post("/{session_id}/complete")
async def complete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Mark session as complete."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_complete = True
    session.ended_at = datetime.now(timezone.utc)
    return {"session_id": session_id, "status": "completed"}
