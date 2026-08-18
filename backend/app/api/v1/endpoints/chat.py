"""
Chat endpoint — full pipeline:
  1. Crisis detection (keyword regex — BYPASSES LLM)
  2. Likert response parsing (questionnaire states)
  3. State machine transition
  4. Response generation (scripted first, LLM if key configured)
  5. Persist to database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.core.database import get_db
from app.models.session import Session
from app.models.screening_response import ScreeningResponse
from app.models.crisis_event import CrisisEvent
from app.crisis.detector import crisis_detector
from app.chatbot.scripted_responses import (
    get_scripted_response,
    get_clarification_response,
)
from app.chatbot.screening_flow import (
    get_next_question,
    parse_likert_response,
    next_instrument_state,
    INSTRUMENT_CONFIG,
)
from app.core.config import settings

router = APIRouter()


def _has_llm_key() -> bool:
    """Check if any LLM API key is configured."""
    if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key-here":
        return True
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10:
        return True
    return False


async def _get_llm_response(user_message: str, history: List, state: str, responses: Dict, pending_item: Optional[Dict]) -> Optional[str]:
    """Try LLM response. Returns None if no key or on failure."""
    if not _has_llm_key():
        return None
    try:
        from app.chatbot.conversation_engine import get_conversation_engine
        engine = get_conversation_engine()
        return await engine.generate_response(
            user_message=user_message,
            conversation_history=history,
            current_state=state,
            responses=responses,
            pending_item=pending_item,
        )
    except Exception as e:
        print(f"[LLM] Failed, falling back to scripted: {e}")
        return None


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
    """Full chat pipeline with scripted fallback — works without any API key."""

    # ── 1. Load session ──────────────────────────────────────────
    result = await db.execute(select(Session).where(Session.id == data.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_state = session.current_state

    # ── 2. Crisis detection (BYPASSES everything else) ───────────
    crisis_result = crisis_detector.detect(data.message)
    if crisis_result.is_crisis:
        event = CrisisEvent(
            session_id=session.id,
            trigger_type=crisis_result.trigger_type,
            trigger_phrase=crisis_result.trigger_phrase,
            confidence=crisis_result.confidence,
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

    # ── 3. Load existing responses for this session ──────────────
    resp_result = await db.execute(
        select(ScreeningResponse).where(ScreeningResponse.session_id == session.id)
    )
    all_responses: Dict = {}
    for r in resp_result.scalars().all():
        if r.instrument not in all_responses:
            all_responses[r.instrument] = {}
        all_responses[r.instrument][r.item_number] = r.response_value

    # ── 4. Questionnaire states: parse Likert answer ─────────────
    pending_item = None
    clarification_needed = False

    if current_state in ("phq9", "gad7", "pss10"):
        existing = all_responses.get(current_state, {})
        pending_item = get_next_question(current_state, existing)

        if pending_item:
            instrument_options = INSTRUMENT_CONFIG[current_state]["options"]
            parsed_val = parse_likert_response(data.message, instrument_options)

            if parsed_val is not None:
                # Valid response — save it
                sr = ScreeningResponse(
                    session_id=session.id,
                    instrument=current_state,
                    item_number=pending_item["item_number"],
                    response_value=parsed_val,
                )
                db.add(sr)
                existing[pending_item["item_number"]] = parsed_val

                total_items = INSTRUMENT_CONFIG[current_state]["total"]
                if len(existing) >= total_items:
                    # Instrument complete — transition
                    next_state = next_instrument_state(current_state)
                    session.current_state = next_state
                    current_state = next_state
                    pending_item = get_next_question(next_state, {}) if next_state in ("phq9", "gad7", "pss10") else None
                else:
                    pending_item = get_next_question(current_state, existing)
            else:
                # Unclear response — ask for clarification
                clarification_needed = True

    # ── 5. Non-questionnaire state transitions ────────────────────
    elif current_state == "greeting":
        session.current_state = "consent"
        current_state = "consent"

    elif current_state == "consent":
        msg_lower = data.message.lower()
        if any(w in msg_lower for w in ["yes", "agree", "ok", "sure", "accept", "ready", "understand", "begin", "start", "i do", "yep", "yeah"]):
            session.current_state = "background"
            current_state = "background"

    elif current_state == "background":
        session.current_state = "phq9"
        current_state = "phq9"
        pending_item = get_next_question("phq9", {})

    # Mark session complete
    if current_state == "results" and not session.is_complete:
        session.is_complete = True

    # ── 6. Generate bot response ──────────────────────────────────
    if clarification_needed and pending_item:
        bot_message = get_clarification_response(pending_item)
    else:
        # Try LLM first; fall back to scripted
        bot_message = await _get_llm_response(
            user_message=data.message,
            history=data.conversation_history or [],
            state=current_state,
            responses=all_responses,
            pending_item=pending_item,
        )
        if not bot_message:
            bot_message = get_scripted_response(
                current_state=current_state,
                user_message=data.message,
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
