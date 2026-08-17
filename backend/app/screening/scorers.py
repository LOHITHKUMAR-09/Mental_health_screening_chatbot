"""
Mental Health Screening Engine — Deterministic Scoring Module.

Implements PHQ-9, GAD-7, and PSS-10 scoring with clinical cutoffs.
This module is COMPLETELY ISOLATED from any LLM — 100% deterministic.
"""

from dataclasses import dataclass
from typing import Dict, Optional


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class InstrumentScore:
    instrument: str
    total: int
    severity: str
    items_answered: int
    items_total: int

    @property
    def is_complete(self) -> bool:
        return self.items_answered == self.items_total


@dataclass
class CompositeRiskResult:
    phq9: InstrumentScore
    gad7: InstrumentScore
    pss10: InstrumentScore
    composite_risk: str  # low | moderate | high
    notes: list[str]


# ── PHQ-9 Scorer ──────────────────────────────────────────────────

class PHQ9Scorer:
    """
    PHQ-9: Patient Health Questionnaire — 9-item Depression Scale.
    Items 1–9, each scored 0 (Not at all) to 3 (Nearly every day).
    Total range: 0–27.
    
    Reference: Kroenke K, Spitzer RL, Williams JBW. (2001).
    """

    ITEMS_TOTAL = 9
    MAX_SCORE = 27

    QUESTIONS = {
        1: "Over the last 2 weeks, how often have you been bothered by little interest or pleasure in doing things?",
        2: "Feeling down, depressed, or hopeless?",
        3: "Trouble falling or staying asleep, or sleeping too much?",
        4: "Feeling tired or having little energy?",
        5: "Poor appetite or overeating?",
        6: "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
        7: "Trouble concentrating on things, such as reading the newspaper or watching television?",
        8: "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless?",
        9: "Thoughts that you would be better off dead, or of hurting yourself in some way?",
    }

    OPTIONS = {
        0: "Not at all",
        1: "Several days",
        2: "More than half the days",
        3: "Nearly every day",
    }

    @staticmethod
    def score(responses: Dict[int, int]) -> InstrumentScore:
        """Compute PHQ-9 score from item responses."""
        total = sum(responses.get(i, 0) for i in range(1, 10))
        items_answered = len([k for k in responses if 1 <= k <= 9])

        if total <= 4:
            severity = "minimal"
        elif total <= 9:
            severity = "mild"
        elif total <= 14:
            severity = "moderate"
        elif total <= 19:
            severity = "moderately_severe"
        else:
            severity = "severe"

        return InstrumentScore(
            instrument="phq9",
            total=total,
            severity=severity,
            items_answered=items_answered,
            items_total=PHQ9Scorer.ITEMS_TOTAL,
        )

    @staticmethod
    def is_suicidal_ideation(responses: Dict[int, int]) -> bool:
        """Returns True if item 9 (suicidal ideation) is scored >= 1."""
        return responses.get(9, 0) >= 1


# ── GAD-7 Scorer ──────────────────────────────────────────────────

class GAD7Scorer:
    """
    GAD-7: Generalized Anxiety Disorder — 7-item Scale.
    Items 1–7, each scored 0–3.
    Total range: 0–21.
    
    Reference: Spitzer RL, et al. (2006).
    """

    ITEMS_TOTAL = 7
    MAX_SCORE = 21

    QUESTIONS = {
        1: "Over the last 2 weeks, how often have you been bothered by feeling nervous, anxious, or on edge?",
        2: "Not being able to stop or control worrying?",
        3: "Worrying too much about different things?",
        4: "Trouble relaxing?",
        5: "Being so restless that it is hard to sit still?",
        6: "Becoming easily annoyed or irritable?",
        7: "Feeling afraid, as if something awful might happen?",
    }

    OPTIONS = {
        0: "Not at all",
        1: "Several days",
        2: "More than half the days",
        3: "Nearly every day",
    }

    @staticmethod
    def score(responses: Dict[int, int]) -> InstrumentScore:
        """Compute GAD-7 score from item responses."""
        total = sum(responses.get(i, 0) for i in range(1, 8))
        items_answered = len([k for k in responses if 1 <= k <= 7])

        if total <= 4:
            severity = "minimal"
        elif total <= 9:
            severity = "mild"
        elif total <= 14:
            severity = "moderate"
        else:
            severity = "severe"

        return InstrumentScore(
            instrument="gad7",
            total=total,
            severity=severity,
            items_answered=items_answered,
            items_total=GAD7Scorer.ITEMS_TOTAL,
        )


# ── PSS-10 Scorer ─────────────────────────────────────────────────

class PSS10Scorer:
    """
    PSS-10: Perceived Stress Scale — 10-item Version.
    Items 1–10, each scored 0 (Never) to 4 (Very often).
    Items 4, 5, 7, 8 are REVERSE SCORED.
    Total range: 0–40.
    
    Reference: Cohen S, Kamarck T, Mermelstein R. (1983).
    """

    ITEMS_TOTAL = 10
    MAX_SCORE = 40
    REVERSE_ITEMS = {4, 5, 7, 8}

    QUESTIONS = {
        1:  "In the last month, how often have you been upset because of something that happened unexpectedly?",
        2:  "Felt that you were unable to control the important things in your life?",
        3:  "Felt nervous and stressed?",
        4:  "Felt confident about your ability to handle your personal problems?",   # Reverse
        5:  "Felt that things were going your way?",                                 # Reverse
        6:  "Found that you could not cope with all the things that you had to do?",
        7:  "Been able to control irritations in your life?",                        # Reverse
        8:  "Felt that you were on top of things?",                                  # Reverse
        9:  "Been angered because of things that happened that were outside of your control?",
        10: "Felt difficulties were piling up so high that you could not overcome them?",
    }

    OPTIONS = {
        0: "Never",
        1: "Almost never",
        2: "Sometimes",
        3: "Fairly often",
        4: "Very often",
    }

    @staticmethod
    def score(responses: Dict[int, int]) -> InstrumentScore:
        """Compute PSS-10 score from item responses, applying reverse scoring."""
        total = 0
        for item_num in range(1, 11):
            val = responses.get(item_num, 0)
            if item_num in PSS10Scorer.REVERSE_ITEMS:
                total += (4 - val)
            else:
                total += val
        items_answered = len([k for k in responses if 1 <= k <= 10])

        if total <= 13:
            severity = "low"
        elif total <= 26:
            severity = "moderate"
        else:
            severity = "high"

        return InstrumentScore(
            instrument="pss10",
            total=total,
            severity=severity,
            items_answered=items_answered,
            items_total=PSS10Scorer.ITEMS_TOTAL,
        )


# ── Composite Risk Calculator ─────────────────────────────────────

class CompositeRiskCalculator:
    """
    Combines PHQ-9, GAD-7, and PSS-10 scores into a single
    composite risk level: low | moderate | high.
    
    Uses weighted normalization. Weights based on clinical significance
    of each instrument for university student populations.
    """

    PHQ9_WEIGHT  = 0.40
    GAD7_WEIGHT  = 0.35
    PSS10_WEIGHT = 0.25

    @staticmethod
    def compute(phq9: InstrumentScore, gad7: InstrumentScore, pss10: InstrumentScore) -> CompositeRiskResult:
        """Compute composite risk from three instrument scores."""
        notes = []

        # Normalize to 0-1 range
        phq9_norm  = phq9.total  / 27.0
        gad7_norm  = gad7.total  / 21.0
        pss10_norm = pss10.total / 40.0

        composite = (
            phq9_norm  * CompositeRiskCalculator.PHQ9_WEIGHT +
            gad7_norm  * CompositeRiskCalculator.GAD7_WEIGHT +
            pss10_norm * CompositeRiskCalculator.PSS10_WEIGHT
        )

        # Severity override: if any single scale is severe, elevate to high
        if phq9.severity in ("moderately_severe", "severe") or gad7.severity == "severe":
            composite_risk = "high"
            notes.append("Elevated to high risk due to severe single-scale score.")
        elif composite < 0.30:
            composite_risk = "low"
        elif composite < 0.55:
            composite_risk = "moderate"
        else:
            composite_risk = "high"

        return CompositeRiskResult(
            phq9=phq9,
            gad7=gad7,
            pss10=pss10,
            composite_risk=composite_risk,
            notes=notes,
        )
