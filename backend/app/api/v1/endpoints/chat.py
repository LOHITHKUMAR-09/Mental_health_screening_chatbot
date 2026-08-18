"""
Chat endpoint — handles user messages through the full pipeline:
  1. Crisis detection (keyword layer) — runs BEFORE LLM
  2. Likert response parsing (if in screening state)
  3. State machine transition
  4. LLM response generation
  5. Persist to database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict
import json

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.session import Session
from app.models.screening_response import ScreeningResponse
from app.models.crisis_event import CrisisEvent
from app.crisis.detector import crisis_detector
from app.chatbot.conversation_engine import get_conversation_engine
from app.chatbot.screening_flow import (
    get_next_question,
    parse_likert_response,
    next_instrument_state,
    INSTRUMENT_CONFIG,
)

router = APIRouter()


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    conversation_history: Optional[List[Dict]] = []


class ChatMessageResponse(BaseModel):
    session_id: str
    bot_message: str
    current_state: str
    is_crisis: bool = False
    crisis_resources: Optional[Dict] = None
    questionnaire_item: Optional[Dict] = None
    screening_complete: bool = False


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(data: ChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """
    Full chat pipeline: crisis check → screening parse → LLM response → state transition.
    """
    # ── 1. Load session ───────────────────────────────────────────
    result = await db.execute(select(Session).where(Session.id == data.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_state = session.current_state

    # ── 2. Crisis detection (BYPASSES LLM) ───────────────────────
    crisis_result = crisis_detector.detect(data.message)
    if crisis_result.is_crisis:
        # Log the crisis event
        event = CrisisEvent(
            session_id=session.id,
            trigger_type=crisis_result.trigger_type,
            trigger_phrase=crisis_result.trigger_phrase,
            response_sent=crisis_result.response,
        )
        db.add(event)
        return ChatMessageResponse(
            session_id=data.session_id,
            bot_message=crisis_result.response,
            current_state=current_state,
            is_crisis=True,
            crisis_resources=crisis_result.crisis_resources,
        )

    # ── 3. Screening state: parse Likert response ─────────────────
    pending_item = None
    if current_state in ("phq9", "gad7", "pss10"):
        # Load existing responses for this instrument in this session
        resp_result = await db.execute(
            select(ScreeningResponse).where(
                ScreeningResponse.session_id == session.id,
                ScreeningResponse.instrument == current_state,
            )
        )
        existing = {r.item_number: r.response_value for r in resp_result.scalars().all()}

        # What's the current question we're waiting on?
        pending_item = get_next_question(current_state, existing)

        if pending_item:
            instrument_options = INSTRUMENT_CONFIG[current_state]["options"]
            parsed_val = parse_likert_response(data.message, instrument_options)
            if parsed_val is not None:
                # Record the response
                sr = ScreeningResponse(
                    session_id=session.id,
                    instrument=current_state,
                    item_number=pending_item["item_number"],
                    response_value=parsed_val,
                )
                db.add(sr)
                existing[pending_item["item_number"]] = parsed_val

                # Check if this instrument is now complete
                total_items = INSTRUMENT_CONFIG[current_state]["total"]
                if len(existing) >= total_items:
                    # Transition to next state
                    next_state = next_instrument_state(current_state)
                    session.current_state = next_state
                    current_state = next_state
                    pending_item = None
                    if next_state in ("phq9", "gad7", "pss10"):
                        pending_item = get_next_question(next_state, {})
                else:
                    # Get next question in same instrument
                    pending_item = get_next_question(current_state, existing)

    # Handle greeting/consent/background state transitions
    elif current_state in ("greeting", "consent", "background"):
        msg_lower = data.message.lower()
        if current_state == "greeting":
            session.current_state = "consent"
            current_state = "consent"
        elif current_state == "consent":
            if any(w in msg_lower for w in ["yes", "agree", "ok", "sure", "accept", "ready", "understand", "i do"]):
                session.current_state = "background"
                current_state = "background"
        elif current_state == "background":
            # After one background exchange, move to PHQ-9
            session.current_state = "phq9"
            current_state = "phq9"
            pending_item = get_next_question("phq9", {})

    # Mark session complete if results state reached
    if current_state == "results" and not session.is_complete:
        session.is_complete = True

    # ── 4. LLM response generation ────────────────────────────────
    engine = get_conversation_engine()
    # Build responses dict for context
    resp_result = await db.execute(
        select(ScreeningResponse).where(ScreeningResponse.session_id == session.id)
    )
    all_responses: Dict = {}
    for r in resp_result.scalars().all():
        if r.instrument not in all_responses:
            all_responses[r.instrument] = {}
        all_responses[r.instrument][r.item_number] = r.response_value

    bot_message = await engine.generate_response(
        user_message=data.message,
        conversation_history=data.conversation_history or [],
        current_state=current_state,
        responses=all_responses,
        pending_item=pending_item,
    )

    return ChatMessageResponse(
        session_id=data.session_id,
        bot_message=bot_message,
        current_state=current_state,
        is_crisis=False,
        questionnaire_item=pending_item,
        screening_complete=(current_state == "results"),
    )
