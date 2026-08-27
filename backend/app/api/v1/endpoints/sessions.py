"""Session management endpoints with conversation history retrieval."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.session import ScreeningSession
from app.models.message import ChatMessage
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
    """Start a new screening session."""
    if not user_id:
        user = User(role="student", is_anonymous=True)
        db.add(user)
        await db.flush()
        user_id = str(user.id)

    count_result = await db.execute(
        select(func.count()).where(ScreeningSession.user_id == user_id)
    )
    session_count = count_result.scalar() or 0

    new_session = ScreeningSession(
        user_id=user_id,
        current_state="greeting",
        session_number=session_count + 1,
    )
    db.add(new_session)
    await db.flush()

    return SessionStartResponse(
        session_id=str(new_session.id),
        current_state="greeting",
        message="Session started. MindEase is ready.",
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
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
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
