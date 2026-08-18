"""
Conversation Engine — LangChain-powered chatbot with stateful session management.
Handles the full screening flow: greeting → consent → background → PHQ-9 → GAD-7 → PSS-10 → results.
"""

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.chatbot.system_prompt import MINDEASE_SYSTEM_PROMPT
from app.chatbot.screening_flow import (
    get_next_question,
    parse_likert_response,
    SCREENING_FLOW,
)


def get_llm():
    """Return the configured LLM provider."""
    if settings.LLM_PROVIDER == "groq":
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
    else:
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )


class ConversationEngine:
    """
    Manages a single chat session with the LLM.
    Maintains conversation history and drives the screening state machine.
    """

    def __init__(self):
        self.llm = get_llm()

    def build_state_context(self, state: str, responses: Dict, pending_item: Optional[Dict]) -> str:
        """Build state-specific context injected into the system prompt."""
        lines = [f"\n\n## Current Session State: {state.upper()}"]

        if state in ("phq9", "gad7", "pss10"):
            answered = responses.get(state, {})
            instrument_map = {"phq9": 9, "gad7": 7, "pss10": 10}
            total_items = instrument_map.get(state, 9)
            lines.append(f"Questions answered so far: {len(answered)}/{total_items}")

            if pending_item:
                lines.append(f"\nYou MUST ask EXACTLY this question next (do NOT rephrase the meaning, you may make it conversational):")
                lines.append(f"Question {pending_item['item_number']}: {pending_item['question']}")
                lines.append(f"Scale: {pending_item['options_str']}")
                lines.append(f"After asking, WAIT for the user's response. Do NOT guess their answer.")

        return "\n".join(lines)

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        current_state: str,
        responses: Dict,
        pending_item: Optional[Dict] = None,
    ) -> str:
        """
        Generate the bot's next response using the LLM.

        Args:
            user_message: The latest user input.
            conversation_history: List of {role: user|assistant, content: str} dicts.
            current_state: Current screening state machine state.
            responses: Dict of collected screening responses so far.
            pending_item: Next questionnaire item to ask, if any.

        Returns:
            The bot's response string.
        """
        state_context = self.build_state_context(current_state, responses, pending_item)
        full_system = MINDEASE_SYSTEM_PROMPT + state_context

        messages = [SystemMessage(content=full_system)]

        # Add conversation history
        for msg in conversation_history[-12:]:  # Keep last 12 turns for context
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        response = await self.llm.ainvoke(messages)
        return response.content


# Module-level singleton
_engine: Optional[ConversationEngine] = None


def get_conversation_engine() -> ConversationEngine:
    """Get or create the singleton conversation engine."""
    global _engine
    if _engine is None:
        _engine = ConversationEngine()
    return _engine
