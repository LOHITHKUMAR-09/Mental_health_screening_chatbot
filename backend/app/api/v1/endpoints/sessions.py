"""Session management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_db

router = APIRouter()


class SessionStartResponse(BaseModel):
    session_id: str
    current_state: str
    message: str


class SessionStateResponse(BaseModel):
    session_id: str
    current_state: str
    is_complete: bool
    started_at: str


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(db: AsyncSession = Depends(get_db)):
    """Start a new screening session."""
    # TODO: Validate JWT token, get user_id
    # TODO: Create session in DB
    # TODO: Return session_id and initial greeting
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "current_state": "greeting",
        "message": "Session started. Let's begin.",
    }


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get current state of a session."""
    # TODO: Query session from DB
    return {
        "session_id": session_id,
        "current_state": "greeting",
        "is_complete": False,
        "started_at": "2026-01-01T00:00:00Z",
    }


@router.post("/{session_id}/complete")
async def complete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Mark session as complete and trigger scoring."""
    # TODO: Mark session complete, trigger ML scoring
    return {"session_id": session_id, "status": "completed"}
