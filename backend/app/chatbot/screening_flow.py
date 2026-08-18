"""
Screening flow definitions — questionnaire questions, options, and state transitions.
This is the authoritative source for PHQ-9, GAD-7, PSS-10 item text and Likert scales.
"""

from typing import Optional, Dict, List, Any

# ── PHQ-9 Questions ───────────────────────────────────────────────
PHQ9_QUESTIONS = {
    1:  "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
    2:  "How often have you felt down, depressed, or hopeless?",
    3:  "How often have you had trouble falling or staying asleep, or slept too much?",
    4:  "How often have you felt tired or had little energy?",
    5:  "How often have you had poor appetite or were overeating?",
    6:  "How often have you felt bad about yourself, or that you are a failure, or have let yourself or your family down?",
    7:  "How often have you had trouble concentrating on things like studying, reading, or watching TV?",
    8:  "How often have you been moving or speaking so slowly that others could have noticed? Or the opposite — being fidgety or restless?",
    9:  "Over the last 2 weeks, have you had any thoughts that you would be better off dead, or thoughts of hurting yourself?",
}

PHQ9_OPTIONS = {
    0: "Not at all",
    1: "Several days",
    2: "More than half the days",
    3: "Nearly every day",
}

# ── GAD-7 Questions ───────────────────────────────────────────────
GAD7_QUESTIONS = {
    1:  "Over the last 2 weeks, how often have you felt nervous, anxious, or on edge?",
    2:  "How often have you been unable to stop or control worrying?",
    3:  "How often have you worried too much about different things?",
    4:  "How often have you had trouble relaxing?",
    5:  "How often have you been so restless that it was hard to sit still?",
    6:  "How often have you become easily annoyed or irritable?",
    7:  "How often have you felt afraid, as if something awful might happen?",
}

GAD7_OPTIONS = {
    0: "Not at all",
    1: "Several days",
    2: "More than half the days",
    3: "Nearly every day",
}

# ── PSS-10 Questions ──────────────────────────────────────────────
PSS10_QUESTIONS = {
    1:  "In the last month, how often have you been upset because of something that happened unexpectedly?",
    2:  "How often have you felt unable to control the important things in your life?",
    3:  "How often have you felt nervous and stressed?",
    4:  "How often have you felt confident about your ability to handle your personal problems?",
    5:  "How often have you felt that things were going your way?",
    6:  "How often have you found that you could not cope with all the things you had to do?",
    7:  "How often have you been able to control irritations in your life?",
    8:  "How often have you felt that you were on top of things?",
    9:  "How often have you been angered because of things that happened outside your control?",
    10: "How often have you felt that difficulties were piling up so high that you could not overcome them?",
}

PSS10_OPTIONS = {
    0: "Never",
    1: "Almost never",
    2: "Sometimes",
    3: "Fairly often",
    4: "Very often",
}

# ── Screening state flow ──────────────────────────────────────────
SCREENING_FLOW = ["greeting", "consent", "background", "phq9", "gad7", "pss10", "results"]

INSTRUMENT_CONFIG = {
    "phq9":  {"questions": PHQ9_QUESTIONS,  "options": PHQ9_OPTIONS,  "total": 9},
    "gad7":  {"questions": GAD7_QUESTIONS,  "options": GAD7_OPTIONS,  "total": 7},
    "pss10": {"questions": PSS10_QUESTIONS, "options": PSS10_OPTIONS, "total": 10},
}


def get_options_str(options: Dict[int, str]) -> str:
    return " | ".join([f"{k}={v}" for k, v in options.items()])


def get_next_question(instrument: str, answered: Dict[int, int]) -> Optional[Dict]:
    """Return the next unanswered question for an instrument, or None if done."""
    config = INSTRUMENT_CONFIG.get(instrument)
    if not config:
        return None
    for i in range(1, config["total"] + 1):
        if i not in answered:
            return {
                "instrument": instrument,
                "item_number": i,
                "question": config["questions"][i],
                "options": config["options"],
                "options_str": get_options_str(config["options"]),
                "total_items": config["total"],
            }
    return None  # All answered


def parse_likert_response(user_text: str, options: Dict[int, str]) -> Optional[int]:
    """
    Parse a Likert-scale response from free text.
    Accepts both numeric (0, 1, 2, 3) and text ("Not at all", "several days").
    Returns the integer value or None if unparseable.
    """
    text = user_text.strip().lower()

    # Direct numeric
    for val in options.keys():
        if text == str(val):
            return val

    # Text matching (case-insensitive, partial)
    for val, label in options.items():
        if label.lower() in text or text in label.lower():
            return val

    # Common aliases
    aliases = {
        "never": 0, "no": 0, "not really": 0, "nope": 0,
        "sometimes": 1, "a bit": 1, "a little": 1, "slightly": 1,
        "often": 2, "frequently": 2, "mostly": 2, "quite a lot": 2,
        "always": 3, "every day": 3, "constantly": 3, "all the time": 3, "yes": 3,
    }
    for alias, val in aliases.items():
        if alias in text:
            return val

    return None


def next_instrument_state(current_state: str) -> str:
    """Return the next state after completing an instrument."""
    transitions = {
        "greeting": "consent",
        "consent": "background",
        "background": "phq9",
        "phq9": "gad7",
        "gad7": "pss10",
        "pss10": "results",
        "results": "results",
    }
    return transitions.get(current_state, "results")
