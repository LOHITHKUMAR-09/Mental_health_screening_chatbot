"""
Scripted / Rule-Based Chatbot Responses.

Works WITHOUT any LLM API key.
Generates contextually appropriate responses for each screening state.
Used as the primary response engine (LLM is optional enhancement).
"""

from typing import Optional, Dict
from app.chatbot.screening_flow import get_next_question, INSTRUMENT_CONFIG


import re

def is_explicit_refusal(msg_lower: str) -> bool:
    """Check if the user is explicitly declining or canceling."""
    # Exclude common non-refusal phrases first
    false_positives = ["nothing", "not much", "not really", "not bad", "not at all", "no problem", "no worries", "no stress"]
    if any(fp in msg_lower for fp in false_positives):
        return False
    refusal_patterns = [r"\bno\b", r"\bnope\b", r"\bcancel\b", r"\bstop\b", r"\bquit\b", r"\bexit\b", r"\bdon'?t\b"]
    return any(re.search(pat, msg_lower) for pat in refusal_patterns)


def get_scripted_response(
    current_state: str,
    user_message: str,
    responses: Dict,
    pending_item: Optional[Dict] = None,
) -> str:
    """
    Generate a warm, contextual response purely based on the screening state.
    No LLM required.
    """
    msg_lower = user_message.lower().strip()

    if current_state == "greeting":
        return (
            "Hello! I'm MindEase, your confidential mental health check-in companion. 💙\n\n"
            "This is a brief, private screening covering how you've been feeling lately. "
            "It takes about 8-10 minutes and covers three areas: mood, anxiety, and stress.\n\n"
            "Before we begin, please note: this is a screening tool only — not a diagnosis. "
            "Everything you share stays private.\n\n"
            "Are you ready to begin? (Type 'Yes' to start)"
        )

    elif current_state in ("consent", "consent_declined"):
        if is_explicit_refusal(msg_lower):
            return (
                "That's completely okay. You can come back whenever you feel ready. "
                "If you ever need support, remember iCall is always available: 9152987821. 💙"
            )
        return (
            "Thank you for trusting MindEase. 🌿\n\n"
            "Just a quick note before we start:\n"
            "• Your responses are private and encrypted\n"
            "• This is not a diagnostic tool\n"
            "• If you feel distressed at any point, crisis support is available immediately\n\n"
            "Let's begin with a few background questions. "
            "What year of study are you in, and what's been on your mind lately?"
        )

    elif current_state == "background":
        return (
            "Thank you for sharing that. It sounds like you're carrying quite a bit right now. "
            "You've taken a positive step just by being here. 🌿\n\n"
            "We'll now go through some standardised questions to better understand how you've been feeling. "
            "For each question, I'll give you response options to choose from.\n\n"
            "Let's start with the first section — about your mood over the last 2 weeks.\n\n"
            + _ask_pending_item(pending_item)
        )

    elif current_state in ("phq9", "gad7", "pss10"):
        return _handle_questionnaire_state(current_state, msg_lower, responses, pending_item)

    elif current_state == "results":
        return (
            "You've completed all the questions — well done for taking this step. 💙\n\n"
            "Your results are being calculated now. "
            "Please click 'View Results' or wait a moment — your personalised summary with scores, "
            "risk level, and coping suggestions is ready.\n\n"
            "Remember: whatever the results show, support is available. "
            "You are not alone. 🌿"
        )

    return "I'm here with you. Could you tell me a bit more about how you're feeling?"


def _ask_pending_item(pending_item: Optional[Dict]) -> str:
    """Format the next questionnaire item as a conversational question."""
    if not pending_item:
        return ""

    instrument = pending_item["instrument"]
    item_num = pending_item["item_number"]
    total = pending_item["total_items"]
    question = pending_item["question"]
    options = pending_item["options"]

    # Format options as a numbered list
    options_text = "\n".join([f"  {k} — {v}" for k, v in options.items()])

    section_labels = {"phq9": "Mood (PHQ-9)", "gad7": "Anxiety (GAD-7)", "pss10": "Stress (PSS-10)"}
    section = section_labels.get(instrument, instrument.upper())

    return (
        f"**{section} — Question {item_num} of {total}**\n\n"
        f"{question}\n\n"
        f"Please reply with a number (0–{max(options.keys())}):\n"
        f"{options_text}"
    )


def _handle_questionnaire_state(
    state: str,
    msg_lower: str,
    responses: Dict,
    pending_item: Optional[Dict],
) -> str:
    """Generate response during questionnaire sections."""

    # If there's no pending item, the instrument is complete
    if not pending_item:
        section_done_messages = {
            "phq9": "Thank you — that completes the mood section. 🌿\n\nNow let's look at anxiety. Again, think about the last 2 weeks.\n\n",
            "gad7": "Thank you — anxiety section complete. 🌿\n\nFinally, we'll look at stress levels over the past month.\n\n",
            "pss10": "That completes all the questions! 🌿\n\nThank you for answering everything honestly. Your results are now being processed.",
        }
        return section_done_messages.get(state, "Section complete. Moving on...")

    # Check if the response was unclear (couldn't be parsed)
    options = pending_item["options"]
    options_text = "\n".join([f"  {k} — {v}" for k, v in options.items()])
    max_val = max(options.keys())

    acknowledgements = [
        "Thank you for sharing that.",
        "I appreciate your honesty.",
        "Got it, thank you.",
        "Thanks for letting me know.",
    ]

    # Pick acknowledgement based on item number to vary it
    item_num = pending_item.get("item_number", 1)
    ack = acknowledgements[(item_num - 1) % len(acknowledgements)]

    # If we're asking the next question
    return (
        f"{ack}\n\n"
        + _ask_pending_item(pending_item)
    )


def get_clarification_response(pending_item: Dict) -> str:
    """Called when user response couldn't be parsed as a Likert value."""
    options = pending_item["options"]
    max_val = max(options.keys())
    options_text = "\n".join([f"  {k} — {v}" for k, v in options.items()])

    return (
        f"Sorry, I didn't quite catch that. 😊\n\n"
        f"Please reply with a number from 0 to {max_val}:\n"
        f"{options_text}\n\n"
        f"For example, type **0** for '{options[0]}' or **{max_val}** for '{options[max_val]}'."
    )
