"""
Conversation Engine - LangChain-powered chatbot with stateful session management.
Handles the full screening flow: greeting -> consent -> background -> PHQ-9 -> GAD-7 -> PSS-10 -> results.
Supports both non-streaming and async streaming responses.
"""

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import Optional, List, Dict, Any, AsyncGenerator

from app.core.config import settings
from app.chatbot.system_prompt import MINDEASE_SYSTEM_PROMPT


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
    Manages chat sessions with the LLM.
    Maintains conversation history and drives the screening state machine.
    """

    def __init__(self):
        self.llm = get_llm()

    async def classify_intent(self, user_message: str, current_state: str) -> str:
        """
        Classify user intent semantically using the LLM:
        - 'consent': user agrees, says yes, is ready, or wants to start the screening.
        - 'refusal': user explicitly declines, says no, wants to stop, or cancels.
        - 'chat': user is asking questions, making small talk (like 'how are you'), or chatting.
        """
        prompt = (
            "You are evaluating a university student's message in a mental health check-in companion dialogue.\n"
            f"The current dialogue stage is '{current_state}'.\n\n"
            "Classify the user's message into exactly ONE category:\n"
            "- 'consent': user agrees to start, says yes, is ready, or wants to proceed with the check-in.\n"
            "- 'refusal': user explicitly declines, says no, cancels, or wants to exit.\n"
            "- 'chat': user is asking questions, making small talk (e.g. 'how are you', 'what is this', 'hello'), or discussing thoughts without saying yes.\n\n"
            f"User message: \"{user_message}\"\n"
            "Return ONLY one word in lowercase: 'consent', 'refusal', or 'chat'."
        )
        try:
            res = await self.llm.ainvoke([HumanMessage(content=prompt)])
            text = res.content.strip().lower()
            if "consent" in text:
                return "consent"
            if "refusal" in text or "decline" in text:
                return "refusal"
            return "chat"
        except Exception as e:
            print(f"[classify_intent] LLM error, falling back to rule-based: {e}")
            from app.chatbot.scripted_responses import is_affirmative_consent, is_explicit_refusal
            clean = user_message.lower().strip()
            if is_explicit_refusal(clean):
                return "refusal"
            if is_affirmative_consent(clean):
                return "consent"
            return "chat"

    def build_state_context(self, state: str, responses: Dict, pending_item: Optional[Dict]) -> str:
        """Build state-specific context injected into the system prompt."""
        lines = [f"\n\n## Current Session State: {state.upper()}"]

        if state == "greeting":
            lines.append(
                "Welcome the student warmly. If they ask how you are or make small talk, respond genuinely and warmly. "
                "Let them know you're here to guide them through a confidential check-in when they're ready."
            )
        elif state == "consent":
            lines.append(
                "Explain what the check-in involves (mood, anxiety, stress) in 1-2 friendly sentences. It's completely confidential and not a diagnosis. "
                "If the student asks questions or engages in small talk (e.g. 'how are you'), respond warmly and empathetically to what they said, "
                "then gently invite them to begin when they feel ready (type 'Yes')."
            )
        elif state == "background":
            lines.append(
                "Gently ask what year of study they're in and how they've been feeling recently. "
                "If they chat or ask questions, converse with empathy and warmth."
            )
        elif state in ("phq9", "gad7", "pss10"):
            answered = responses.get(state, {})
            instrument_map = {"phq9": 9, "gad7": 7, "pss10": 10}
            total_items = instrument_map.get(state, 9)
            lines.append(f"Questions answered so far: {len(answered)}/{total_items}")

            if pending_item:
                lines.append(f"\nYou MUST ask EXACTLY this question next (do NOT rephrase the meaning, you may make it conversational):")
                lines.append(f"Question {pending_item['item_number']}: {pending_item['question']}")
                lines.append(f"Scale options: {pending_item['options_str']}")
                lines.append(f"After asking, WAIT for the user's response. Do NOT guess their answer.")
        elif state == "results":
            lines.append(
                "Congratulate the student with compassion on completing the check-in. "
                "Summarize that their responses across depression (PHQ-9), anxiety (GAD-7), and stress (PSS-10) "
                "have been processed, and their personalised summary card and coping suggestions are ready below."
            )

        return "\n".join(lines)

    def _build_messages(
        self,
        user_message: str,
        conversation_history: List[Dict],
        current_state: str,
        responses: Dict,
        pending_item: Optional[Dict] = None,
    ) -> List[Any]:
        state_context = self.build_state_context(current_state, responses, pending_item)
        full_system = MINDEASE_SYSTEM_PROMPT + state_context

        messages = [SystemMessage(content=full_system)]

        for msg in conversation_history[-12:]:
            if msg.get("role") == "user" or msg.get("sender") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            else:
                messages.append(AIMessage(content=msg.get("content", "")))

        messages.append(HumanMessage(content=user_message))
        return messages

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        current_state: str,
        responses: Dict,
        pending_item: Optional[Dict] = None,
    ) -> str:
        """Generate full response synchronously."""
        messages = self._build_messages(user_message, conversation_history, current_state, responses, pending_item)
        response = await self.llm.ainvoke(messages)
        return response.content

    async def generate_response_stream(
        self,
        user_message: str,
        conversation_history: List[Dict],
        current_state: str,
        responses: Dict,
        pending_item: Optional[Dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks asynchronously."""
        messages = self._build_messages(user_message, conversation_history, current_state, responses, pending_item)
        async for chunk in self.llm.astream(messages):
            yield chunk.content


# Module-level singleton
_engine: Optional[ConversationEngine] = None


def get_conversation_engine() -> ConversationEngine:
    """Get or create the singleton conversation engine."""
    global _engine
    if _engine is None:
        _engine = ConversationEngine()
    return _engine
