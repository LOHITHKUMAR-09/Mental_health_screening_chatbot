"""Chat endpoint — handles user messages and returns chatbot replies."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db

router = APIRouter()


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


class ChatMessageResponse(BaseModel):
    session_id: str
    bot_message: str
    current_state: str
    is_crisis: bool = False
    crisis_resources: Optional[dict] = None
    questionnaire_item: Optional[dict] = None  # {instrument, item_number, question_text, options}


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(data: ChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a user message and return the chatbot's response.
    
    Pipeline:
    1. Run crisis detection (keyword layer)
    2. If no crisis: route to LLM conversation engine
    3. If in screening state: record questionnaire response
    4. Return bot message + next questionnaire item if applicable
    """
    # TODO: Step 1 — Crisis detection
    # TODO: Step 2 — LLM conversation engine (LangGraph)
    # TODO: Step 3 — Record screening response if applicable
    # TODO: Step 4 — State transition
    return {
        "session_id": data.session_id,
        "bot_message": "Thank you for sharing. I'm here to listen. [STUB]",
        "current_state": "greeting",
        "is_crisis": False,
    }
