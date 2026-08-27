"""
Chat endpoint - full pipeline with persistent message history & SSE streaming:
  1. Crisis detection (keyword regex - BYPASSES LLM)
  2. Likert response parsing (questionnaire states)
  3. State machine transition
  4. Response generation (LLM if key configured, else scripted)
  5. Save messages to chat_messages table in PostgreSQL
  6. Supports both JSON and SSE streaming endpoints
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, AsyncGenerator

from app.core.database import get_db
from app.models.session import ScreeningSession
from app.models.screening_response import ScreeningResponse
from app.models.crisis_event import CrisisEvent
from app.models.message import ChatMessage
from app.crisis.detector import crisis_detector
from app.chatbot.scripted_responses import get_scripted_response, get_clarification_response
from app.chatbot.screening_flow import (
    get_next_question,
    parse_likert_response,
    next_instrument_state,
    INSTRUMENT_CONFIG,
)
from app.core.config import settings

router = APIRouter()


def _has_llm_key() -> bool:
    if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY and len(settings.GROQ_API_KEY) > 20 and settings.GROQ_API_KEY != "your-groq-api-key-here":
        return True
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 20:
        return True
    return False


async def _get_llm_response(
    user_message: str, history: List, state: str, responses: Dict, pending_item: Optional[Dict]
) -> Optional[str]:
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


async def process_chat_message(data: ChatMessageRequest, db: AsyncSession):
    """Core chat processing logic shared between standard and streaming endpoints."""
    # 1. Load session
    result = await db.execute(select(ScreeningSession).where(ScreeningSession.id == data.session_id))
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    current_state = sess.current_state

    # Save user message
    user_msg_record = ChatMessage(
        session_id=sess.id,
        sender="user",
        content=data.message,
        state=current_state,
    )
    db.add(user_msg_record)

    # 2. Crisis detection (BYPASSES everything else)
    crisis_result = crisis_detector.detect(data.message)
    if crisis_result.is_crisis:
        crisis_msg = crisis_result.response or "Please reach out to emergency resources immediately."
        event = CrisisEvent(
            session_id=sess.id,
            trigger_type=crisis_result.trigger_type,
            trigger_phrase=crisis_result.trigger_phrase,
            confidence=crisis_result.confidence,
            response_sent=crisis_msg,
        )
        db.add(event)

        bot_msg_record = ChatMessage(
            session_id=sess.id,
            sender="bot",
            content=crisis_msg,
            state=current_state,
        )
        db.add(bot_msg_record)
        await db.flush()

        return {
            "sess": sess,
            "bot_message": crisis_msg,
            "current_state": current_state,
            "is_crisis": True,
            "crisis_resources": crisis_result.crisis_resources,
            "pending_item": None,
            "screening_complete": False,
        }

    # 3. Load existing responses for this session
    resp_result = await db.execute(
        select(ScreeningResponse).where(ScreeningResponse.session_id == sess.id)
    )
    all_responses: Dict = {}
    for r in resp_result.scalars().all():
        if r.instrument not in all_responses:
            all_responses[r.instrument] = {}
        all_responses[r.instrument][r.item_number] = r.response_value

    # 4. Questionnaire states: parse Likert answer
    pending_item = None
    clarification_needed = False

    if current_state in ("phq9", "gad7", "pss10"):
        existing = all_responses.get(current_state, {})
        pending_item = get_next_question(current_state, existing)

        if pending_item:
            instrument_options = INSTRUMENT_CONFIG[current_state]["options"]
            parsed_val = parse_likert_response(data.message, instrument_options)

            if parsed_val is not None:
                sr = ScreeningResponse(
                    session_id=sess.id,
                    instrument=current_state,
                    item_number=pending_item["item_number"],
                    response_value=parsed_val,
                )
                db.add(sr)
                existing[pending_item["item_number"]] = parsed_val

                total_items = INSTRUMENT_CONFIG[current_state]["total"]
                if len(existing) >= total_items:
                    next_state = next_instrument_state(current_state)
                    sess.current_state = next_state
                    current_state = next_state
                    pending_item = get_next_question(next_state, {}) if next_state in ("phq9", "gad7", "pss10") else None
                else:
                    pending_item = get_next_question(current_state, existing)
            else:
                clarification_needed = True

    # 5. Non-questionnaire state transitions
    response_state = current_state
    if current_state in ("phq9", "gad7", "pss10"):
        pass  # Handled above
    elif current_state == "greeting":
        sess.current_state = "consent"
        response_state = "greeting"

    elif current_state == "consent":
        from app.chatbot.scripted_responses import is_explicit_refusal
        msg_lower = data.message.lower().strip()
        if is_explicit_refusal(msg_lower):
            sess.current_state = "consent"
            response_state = "consent_declined"
        else:
            sess.current_state = "background"
            current_state = "background"
            response_state = "consent"

    elif current_state == "background":
        sess.current_state = "phq9"
        current_state = "phq9"
        pending_item = get_next_question("phq9", {})
        response_state = "background"

    if current_state == "results" and not sess.is_complete:
        sess.is_complete = True

    # 6. Generate bot response
    if clarification_needed and pending_item:
        bot_message = get_clarification_response(pending_item)
    else:
        bot_message = await _get_llm_response(
            user_message=data.message,
            history=data.conversation_history or [],
            state=current_state,
            responses=all_responses,
            pending_item=pending_item,
        )
        if not bot_message:
            bot_message = get_scripted_response(
                current_state=response_state,
                user_message=data.message,
                responses=all_responses,
                pending_item=pending_item,
            )

    if not bot_message:
        bot_message = "Thank you for your response."

    # Save bot message to DB
    bot_msg_record = ChatMessage(
        session_id=sess.id,
        sender="bot",
        content=bot_message,
        state=current_state,
    )
    db.add(bot_msg_record)
    await db.flush()

    return {
        "sess": sess,
        "bot_message": bot_message,
        "current_state": current_state,
        "is_crisis": False,
        "crisis_resources": None,
        "pending_item": pending_item,
        "screening_complete": (current_state == "results"),
    }


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(data: ChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """Standard JSON chat endpoint."""
    res = await process_chat_message(data, db)
    return ChatMessageResponse(
        session_id=data.session_id,
        bot_message=res["bot_message"],
        current_state=res["current_state"],
        is_crisis=res["is_crisis"],
        crisis_resources=res["crisis_resources"],
        questionnaire_item=res["pending_item"],
        screening_complete=res["screening_complete"],
    )


@router.post("/stream")
async def stream_chat_message(data: ChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """Server-Sent Events (SSE) streaming chat endpoint."""
    res = await process_chat_message(data, db)

    async def event_generator() -> AsyncGenerator[str, None]:
        full_text = res["bot_message"]
        # Stream chunks for real-time typewriter effect in UI
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            payload = json.dumps({
                "chunk": chunk,
                "current_state": res["current_state"],
                "is_crisis": res["is_crisis"],
                "screening_complete": res["screening_complete"],
            })
            yield f"data: {payload}\n\n"

        # Final completion event
        final_payload = json.dumps({
            "done": True,
            "full_message": full_text,
            "current_state": res["current_state"],
            "questionnaire_item": res["pending_item"],
            "crisis_resources": res["crisis_resources"],
            "screening_complete": res["screening_complete"],
        })
        yield f"data: {final_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
