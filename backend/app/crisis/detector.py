"""
Crisis Detection Module - Safety-Critical Component.

This module BYPASSES the LLM entirely. It runs synchronously
on EVERY user message BEFORE any LLM processing.

Architecture:
  Layer 1: Regex/Keyword detection (fast, deterministic, multilingual English + Hinglish)
  Layer 2: [Future] RoBERTa ML classifier
  Layer 3: Hard-coded escalation response (never LLM-generated)
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from app.core.config import settings


# ── Crisis Keywords Dictionary (English + Hinglish) ───────────────

CRISIS_PATTERNS = {
    "suicidal_ideation": [
        r"\bwant(ed)?\s+to\s+die\b",
        r"\bwanna\s+die\b",
        r"\bend\s+(my|this)\s+life\b",
        r"\bkill\s+my(self)?\b",
        r"\bno\s+reason\s+to\s+live\b",
        r"\bbetter\s+off\s+dead\b",
        r"\bsuicid(e|al)\b",
        r"\btake\s+my\s+(own\s+)?life\b",
        r"\bwish\s+i\s+(was|were|am)\s+dead\b",
        r"\bdon'?t\s+want\s+to\s+(be\s+here|exist|live)\b",
        r"\bkms\b",
        r"\bhanging\s+my(self)?\b",
        r"\boverdose\s+on\b",
        # Hinglish / Romanized Hindi phrases
        r"\bmar(na)?\s+(chahta|chahti|chahte)\s+(hu|hoon|h)\b",
        r"\bmar\s+ja(na|unga|ungi)\b",
        r"\bkhud\s*kushi\b",
        r"\bjaan\s+de\s+(dunga|dungi|dena)\b",
        r"\bjeene\s+ka\s+mann\s+nahi\b",
        r"\bzindagi\s+se\s+tang\b",
        r"\bkhatam\s+karna\s+(chahta|chahti|chahte|hun|hoon)\b",
        r"\bkhud\s+ko\s+khatam\b",
        r"\bapni\s+(jaan|zindagi)\s+(lena|khatam)\b",
    ],
    "self_harm": [
        r"\bhurt\s+my(self)?\b",
        r"\bcut\s+my(self)?\b",
        r"\bburning?\s+my(self)?\b",
        r"\bself.?harm\b",
        r"\bself.?injur(e|y|ing)\b",
        r"\bbleed\s+out\b",
        # Hinglish
        r"\bkhud\s+ko\s+nuksan\b",
        r"\bhaath\s+kaat\b",
    ],
    "crisis_distress": [
        r"\bcan'?t\s+(take\s+it|go\s+on)\s+anymore\b",
        r"\bno\s+point\s+in\s+living\b",
        r"\beverything\s+is\s+hopeless\b",
        r"\bfeel\s+completely\s+empty\b",
    ],
}

# Context exceptions (false positive suppression)
SAFE_IDIOM_PATTERNS = [
    r"\bdying\s+of\s+laughter\b",
    r"\blaughing\s+so\s+hard\b",
    r"\b(exam|workload|traffic|assignment|project)\s+(is\s+)?killing\s+me\b",
    r"\bthat\s+joke\s+killed\s+me\b",
]

CRISIS_RESPONSE_TEMPLATE = """
I can hear that you're going through something really difficult right now, and I'm genuinely concerned about you. 💙

**Please reach out to someone who can help right now:**

🆘 **iCall (India):** 9152987821 *(Mon–Sat, 8am–10pm)*
🆘 **Vandrevala Foundation Helpline:** 1860-2662-345 *(24/7, Free)*
🆘 **iCall WhatsApp:** https://wa.me/919152987821

🏥 **Your Campus Counseling Center** - Please contact them immediately today.
🚨 **Emergency Services (India):** Call **112** for immediate emergency assistance.

---
*You do not have to carry this alone. Confidential, compassionate help is ready to support you.*
"""


@dataclass
class CrisisDetectionResult:
    is_crisis: bool
    trigger_type: Optional[str] = None
    trigger_phrase: Optional[str] = None
    confidence: float = 0.0
    response: Optional[str] = None
    crisis_resources: dict = field(default_factory=dict)


class KeywordCrisisDetector:
    """
    Fast regex-based keyword crisis matching (English + Hinglish).
    Runs BEFORE LLM processing on every user turn.
    """

    def __init__(self):
        self._compiled = {
            category: [re.compile(p, re.IGNORECASE) for p in patterns]
            for category, patterns in CRISIS_PATTERNS.items()
        }
        self._safe_compiled = [re.compile(p, re.IGNORECASE) for p in SAFE_IDIOM_PATTERNS]

    def detect(self, text: str) -> CrisisDetectionResult:
        """Scan text for crisis indicators with idiom false positive filtering."""
        clean_text = text.strip()

        # Check for safe idiomatic expressions first
        for safe_p in self._safe_compiled:
            if safe_p.search(clean_text):
                return CrisisDetectionResult(is_crisis=False)

        # Check crisis patterns
        for category, patterns in self._compiled.items():
            for pattern in patterns:
                match = pattern.search(clean_text)
                if match:
                    return CrisisDetectionResult(
                        is_crisis=True,
                        trigger_type=category,
                        trigger_phrase=match.group(0),
                        confidence=1.0,
                        response=CRISIS_RESPONSE_TEMPLATE.strip(),
                        crisis_resources={
                            "icall": {
                                "name": "iCall (India)",
                                "phone": settings.ICALL_HELPLINE,
                                "hours": "Mon–Sat, 8am–10pm",
                            },
                            "vandrevala": {
                                "name": "Vandrevala Foundation",
                                "phone": settings.VANDREVALA_HELPLINE,
                                "hours": "24/7",
                            },
                            "emergency": "112",
                        },
                    )

        return CrisisDetectionResult(is_crisis=False)


# Singleton detector instance
crisis_detector = KeywordCrisisDetector()
