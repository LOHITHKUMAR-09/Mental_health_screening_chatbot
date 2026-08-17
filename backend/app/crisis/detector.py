"""
Crisis Detection Module — Safety-Critical Component.

This module BYPASSES the LLM entirely. It runs synchronously
on EVERY user message BEFORE any LLM processing.

Architecture:
  Layer 1: Regex/Keyword detection (fast, deterministic)
  Layer 2: [Future] RoBERTa ML classifier
  Layer 3: Hard-coded escalation response (never LLM-generated)
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from app.core.config import settings


# ── Crisis Keywords Dictionary ────────────────────────────────────
# Organized by severity and category

CRISIS_PATTERNS = {
    "suicidal_ideation": [
        r"\bwant(ed)?\s+to\s+die\b",
        r"\bend\s+(my|this)\s+life\b",
        r"\bkill\s+my(self)?\b",
        r"\bno\s+reason\s+to\s+live\b",
        r"\bbetter\s+off\s+dead\b",
        r"\bsuicid(e|al)\b",
        r"\btake\s+my\s+(own\s+)?life\b",
        r"\bwish\s+i\s+(was|were|am)\s+dead\b",
        r"\bdon'?t\s+want\s+to\s+(be\s+here|exist|live)\b",
    ],
    "self_harm": [
        r"\bhurt\s+my(self)?\b",
        r"\bcut\s+my(self)?\b",
        r"\bburning?\s+my(self)?\b",
        r"\bself.?harm\b",
        r"\bself.?injur(e|y|ing)\b",
    ],
    "crisis_distress": [
        r"\bcan'?t\s+(take\s+it|go\s+on)\b",
        r"\bgive\s+up\b",
        r"\bno\s+hope\b",
        r"\beverything\s+is\s+(hopeless|pointless)\b",
        r"\bfeel\s+(completely\s+)?empty\b",
    ],
}

CRISIS_RESPONSE_TEMPLATE = """
I can hear that you're going through something really difficult right now, and I'm genuinely concerned about you. 💙

**Please reach out to someone who can help right now:**

🆘 **iCall (India):** 9152987821 *(Mon–Sat, 8am–10pm)*
🆘 **Vandrevala Foundation Helpline:** 1860-2662-345 *(24/7)*
🆘 **iCall WhatsApp:** https://wa.me/919152987821

🏥 **Your campus counseling center** — please visit or call them today.

If you are in immediate danger, please call **112** (Emergency Services) right away.

---
*You don't have to face this alone. Trained counselors are ready to listen. Please make that call.*
"""


# ── Detection Result ──────────────────────────────────────────────

@dataclass
class CrisisDetectionResult:
    is_crisis: bool
    trigger_type: Optional[str] = None      # suicidal_ideation | self_harm | crisis_distress
    trigger_phrase: Optional[str] = None    # The matched phrase
    confidence: float = 0.0                  # 1.0 for keyword matches
    response: Optional[str] = None           # The hardcoded response to send
    crisis_resources: dict = field(default_factory=dict)


# ── Keyword Detector ──────────────────────────────────────────────

class KeywordCrisisDetector:
    """
    Layer 1 crisis detection: fast regex-based keyword matching.
    Returns a CrisisDetectionResult. 
    
    Runs BEFORE the LLM on every single user message.
    """

    def __init__(self):
        # Compile all patterns for performance
        self._compiled = {
            category: [re.compile(p, re.IGNORECASE) for p in patterns]
            for category, patterns in CRISIS_PATTERNS.items()
        }

    def detect(self, text: str) -> CrisisDetectionResult:
        """
        Scan user message text for crisis indicators.
        Returns CrisisDetectionResult with is_crisis=True if any pattern matches.
        """
        for category, patterns in self._compiled.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    return CrisisDetectionResult(
                        is_crisis=True,
                        trigger_type=category,
                        trigger_phrase=match.group(0),
                        confidence=1.0,  # Keyword match = certain
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
