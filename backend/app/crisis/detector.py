"""
Crisis Detection Module - Safety-Critical Component.

This module runs synchronously on EVERY user message BEFORE any LLM processing.

Architecture:
  Layer 1: Semantic context analysis — distinguishes PAST resolved events vs ACTIVE crisis
  Layer 2: Regex/Keyword detection (fast, deterministic, multilingual English + Hinglish)
  Layer 3: Severity scoring — HIGH (active, immediate), MEDIUM (disclosed past, monitoring)
  Layer 4: Contextually appropriate response (empathic but not robotic alarm for past events)
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from app.core.config import settings


# ── Severity Levels ───────────────────────────────────────────────
SEVERITY_HIGH   = "high"    # Active, present-tense crisis → immediate emergency resources
SEVERITY_MEDIUM = "medium"  # Past event disclosed, currently safe → warm acknowledgement + resources


# ── Contextual Modifiers (Semantic Filters) ───────────────────────
# These patterns indicate the crisis was in the PAST or was RESOLVED.
# Match BEFORE the main crisis scan to downgrade severity.
PAST_TENSE_PATTERNS = [
    r"\b(was|were|had|used\s+to|almost|nearly|once|yesterday|today\s+(morning|but)|last\s+(week|month|year))\b.*\b(suicid|kill|hurt|harm|die|end\s+(my|this)\s+life)\b",
    r"\b(suicid|kill|hurt|harm|die|end\s+(my|this)\s+life)\b.*\b(but|however|thankfully|luckily|fortunately|saved|helped|stopped|talked\s+(me|him|her|them)\s+out)\b",
    r"\babout\s+to\s+(suicid|kill\s+my|end\s+my\s+life|hurt\s+my).*\b(but|saved|stopped|friend|family)\b",
    r"\b(almost|nearly)\s+(ended|took|killed|end|take|kill)\s+(my|his|her|their)\s+(life|self)\b",
    r"\b(almost|nearly)\s+(ended|end)\s+(my|his|her|their)\s+(life|self)\b",
    r"\bi\s+(survived|recovered|got\s+help|called|reached\s+out|was\s+saved)\b",
    r"\b(my\s+friend|someone|family|counselor|doctor)\s+(saved|helped|stopped|talked)\s+(me|him|her)\b",
]

# These confirm the crisis is ACTIVE / PRESENT TENSE → HIGH severity
ACTIVE_PRESENT_PATTERNS = [
    r"\b(right\s+now|tonight|today\s+and\s+i\s+(still|feel)|currently|at\s+this\s+moment|i\s+am\s+going\s+to)\b",
    r"\bi\s+(am|'m)\s+(going\s+to|about\s+to|planning\s+to)\b",
    r"\bplease\s+help\s+me\b",
    r"\bi\s+have\s+(pills?|a\s+knife|a\s+weapon|a\s+plan)\b",
    r"\bno\s+one\s+(can|will)\s+(help|save|stop)\s+me\b",
    r"\bgoodbye\b.*\b(forever|for\s+the\s+last\s+time)\b",
]

# False positive / safe idiom suppression
SAFE_IDIOM_PATTERNS = [
    r"\bdying\s+of\s+laughter\b",
    r"\blaughing\s+so\s+hard\b",
    r"\b(exam|workload|traffic|assignment|project|deadline)\s+(is\s+)?killing\s+me\b",
    r"\bthat\s+joke\s+killed\s+me\b",
    r"\bi\s+could\s+kill\s+(for|a)\b",
    r"\bdead\s+tired\b",
    r"\bdead\s+serious\b",
    r"\bdying\s+to\s+(see|know|try|eat|go)\b",
    r"\bkilled\s+it\b",
]


# ── Crisis Keyword Patterns (English + Hinglish) ──────────────────
CRISIS_PATTERNS = {
    "suicidal_ideation": [
        r"\bwant(ed)?\s+to\s+die\b",
        r"\bwanna\s+die\b",
        r"\bend\s+(my|this)\s+life\b",
        r"\bkill\s+my(self)?\b",
        r"\bno\s+reason\s+to\s+live\b",
        r"\bbetter\s+off\s+dead\b",
        r"\bsuicid(e|al|ed|ing)\b",
        r"\btake\s+my\s+(own\s+)?life\b",
        r"\bwish\s+i\s+(was|were|am)\s+dead\b",
        r"\bdon'?t\s+want\s+to\s+(be\s+here|exist|live)\b",
        r"\bkms\b",
        r"\bhanging\s+my(self)?\b",
        r"\boverdose\s+on\b",
        # Hinglish
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
        r"\bkhud\s+ko\s+nuksan\b",
        r"\bhaath\s+kaat\b",
    ],
    "crisis_distress": [
        r"\bcan'?t\s+(take\s+it|go\s+on)\s+anymore\b",
        r"\bno\s+point\s+in\s+living\b",
        r"\beverything\s+is\s+hopeless\b",
        r"\bfeel\s+completely\s+empty\b",
        r"\bi\s+give\s+up\s+on\s+(life|everything)\b",
        r"\bfeel\s+like\s+i\s+(can'?t|cannot)\s+(go\s+on|continue|do\s+this|keep\s+going)\b",
        r"\b(can'?t|cannot)\s+(go\s+on|keep\s+going|continue)\s+(anymore|like\s+this)\b",
        r"\b(can'?t|cannot)\s+see\s+a\s+(reason|point|purpose)\s+to\s+(live|go\s+on|continue)\b",
        r"\bnot\s+worth\s+(living|it|anything)\b",
    ],
}

# ── Response Templates by Severity ───────────────────────────────

# HIGH: Active/immediate crisis — firm, clear resources, empathic urgency
CRISIS_RESPONSE_HIGH = """I hear you, and I'm really concerned about your safety right now. Please reach out for immediate support — you don't have to face this alone. 💙

🆘 **iCall (India):** 9152987821 *(Mon–Sat, 8am–10pm)*
🆘 **Vandrevala Foundation:** 1860-2662-345 *(24/7, Free)*
🚨 **Emergency Services:** **112** *(If you are in immediate danger)*
🆘 **iCall WhatsApp:** https://wa.me/919152987821

Your life has value. Please make that call right now — a trained counselor is ready to listen."""

# MEDIUM: Past event disclosed, person appears safe now — warm, human, continues conversation
CRISIS_RESPONSE_MEDIUM = """Thank you for trusting me with something so personal — that takes real courage. 💙

I'm glad you're here and safe right now. What you went through sounds incredibly difficult, and it matters.

Just so you know, if you ever feel that way again, these are always available to you:
📞 **iCall:** 9152987821 *(Mon–Sat, 8am–10pm)*
📞 **Vandrevala Foundation:** 1860-2662-345 *(24/7, Free)*

Whenever you're ready, I'd like to continue our check-in so we can better understand how you've been feeling overall. Is that okay?"""


@dataclass
class CrisisDetectionResult:
    is_crisis: bool
    severity: str = "none"          # "high", "medium", "none"
    trigger_type: Optional[str] = None
    trigger_phrase: Optional[str] = None
    confidence: float = 0.0
    response: Optional[str] = None
    blocks_flow: bool = False        # True = stop session flow | False = show note, continue
    crisis_resources: dict = field(default_factory=dict)


class KeywordCrisisDetector:
    """
    Semantic-aware crisis detector with severity classification.

    Distinguishes between:
    - ACTIVE crisis (present tense, immediate danger) → HIGH severity, blocks flow
    - DISCLOSED past event (resolved, now safe) → MEDIUM severity, empathic note, continues
    - False positive / safe idioms → not flagged
    """

    def __init__(self):
        self._compiled = {
            category: [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns]
            for category, patterns in CRISIS_PATTERNS.items()
        }
        self._safe_compiled    = [re.compile(p, re.IGNORECASE) for p in SAFE_IDIOM_PATTERNS]
        self._past_compiled    = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in PAST_TENSE_PATTERNS]
        self._present_compiled = [re.compile(p, re.IGNORECASE) for p in ACTIVE_PRESENT_PATTERNS]

    def _build_resources(self) -> dict:
        return {
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
        }

    def detect(self, text: str) -> CrisisDetectionResult:
        """
        Semantic crisis detection with severity classification.

        Detection order:
        1. Safe idiom filter → returns safe immediately
        2. Past-tense crisis patterns → MEDIUM severity (empathic note, continues flow)
        3. Active present crisis keywords → HIGH severity (blocks flow)
        4. Generic crisis keywords (ambiguous) → HIGH severity (clinical safety default)
        """
        clean_text = text.strip()

        # ── Layer 1: Safe idiom filter ────────────────────────────────
        for safe_p in self._safe_compiled:
            if safe_p.search(clean_text):
                return CrisisDetectionResult(is_crisis=False, severity="none")

        # ── Layer 2: Past-tense crisis patterns (check BEFORE keyword scan)
        # These match full resolved-context phrases e.g. "almost ended my life but counselor helped"
        for past_p in self._past_compiled:
            if past_p.search(clean_text):
                return CrisisDetectionResult(
                    is_crisis=True,
                    severity=SEVERITY_MEDIUM,
                    trigger_type="disclosed_past_event",
                    trigger_phrase="past crisis event",
                    confidence=0.7,
                    response=CRISIS_RESPONSE_MEDIUM.strip(),
                    blocks_flow=False,
                    crisis_resources=self._build_resources(),
                )

        # ── Layer 3: Check for crisis keywords ───────────────────────
        matched_category = None
        matched_phrase   = None
        for category, patterns in self._compiled.items():
            for pattern in patterns:
                match = pattern.search(clean_text)
                if match:
                    matched_category = category
                    matched_phrase   = match.group(0)
                    break
            if matched_category:
                break

        if not matched_category:
            return CrisisDetectionResult(is_crisis=False, severity="none")

        # ── Layer 4: Active present-tense check → HIGH ───────────────
        for present_p in self._present_compiled:
            if present_p.search(clean_text):
                return CrisisDetectionResult(
                    is_crisis=True,
                    severity=SEVERITY_HIGH,
                    trigger_type=matched_category,
                    trigger_phrase=matched_phrase,
                    confidence=1.0,
                    response=CRISIS_RESPONSE_HIGH.strip(),
                    blocks_flow=True,
                    crisis_resources=self._build_resources(),
                )

        # ── Layer 5: Ambiguous → HIGH (clinical safety default) ──────
        return CrisisDetectionResult(
            is_crisis=True,
            severity=SEVERITY_HIGH,
            trigger_type=matched_category,
            trigger_phrase=matched_phrase,
            confidence=0.85,
            response=CRISIS_RESPONSE_HIGH.strip(),
            blocks_flow=True,
            crisis_resources=self._build_resources(),
        )


# Singleton detector instance
crisis_detector = KeywordCrisisDetector()
