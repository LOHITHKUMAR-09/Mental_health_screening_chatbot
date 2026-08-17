"""
Feature engineering pipeline for ML mental health risk classification.
Transforms raw questionnaire responses into ML-ready features.
"""

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, List, Optional
from datetime import datetime


# PSS-10 reverse-scored items (1-indexed)
PSS10_REVERSE_ITEMS = {4, 5, 7, 8}

# Item counts per instrument
INSTRUMENT_ITEMS = {
    "phq9": 9,
    "gad7": 7,
    "pss10": 10,
}


def compute_phq9_score(responses: Dict[int, int]) -> tuple[int, str]:
    """
    Compute PHQ-9 total score and severity label.
    Items scored 0-3. Total: 0-27.
    """
    total = sum(responses.get(i, 0) for i in range(1, 10))
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
    return total, severity


def compute_gad7_score(responses: Dict[int, int]) -> tuple[int, str]:
    """
    Compute GAD-7 total score and severity label.
    Items scored 0-3. Total: 0-21.
    """
    total = sum(responses.get(i, 0) for i in range(1, 8))
    if total <= 4:
        severity = "minimal"
    elif total <= 9:
        severity = "mild"
    elif total <= 14:
        severity = "moderate"
    else:
        severity = "severe"
    return total, severity


def compute_pss10_score(responses: Dict[int, int]) -> tuple[int, str]:
    """
    Compute PSS-10 total score and severity label.
    Items scored 0-4. Reverse-scored items: 4, 5, 7, 8.
    Total: 0-40.
    """
    total = 0
    for item_num, val in responses.items():
        if item_num in PSS10_REVERSE_ITEMS:
            total += (4 - val)  # Reverse score
        else:
            total += val

    if total <= 13:
        severity = "low"
    elif total <= 26:
        severity = "moderate"
    else:
        severity = "high"
    return total, severity


def compute_composite_risk(
    phq9_score: int,
    gad7_score: int,
    pss10_score: int,
) -> str:
    """
    Compute composite risk level (low / moderate / high) from three subscale scores.
    Uses a weighted rule-based approach.
    """
    # Normalize each to 0-1 range
    phq9_norm = phq9_score / 27.0
    gad7_norm = gad7_score / 21.0
    pss10_norm = pss10_score / 40.0

    # Weighted composite (equal weighting for baseline)
    composite = (phq9_norm * 0.4) + (gad7_norm * 0.35) + (pss10_norm * 0.25)

    if composite < 0.30:
        return "low"
    elif composite < 0.55:
        return "moderate"
    else:
        return "high"


def build_feature_vector(
    phq9_responses: Dict[int, int],
    gad7_responses: Dict[int, int],
    pss10_responses: Dict[int, int],
    context: Optional[Dict] = None,
) -> Dict[str, float]:
    """
    Build the full feature vector for ML classification.
    
    Features:
    - 26 individual item scores (PHQ-9 x9, GAD-7 x7, PSS-10 x10)
    - 3 subscale totals
    - Derived: max item score per instrument, variance, severe item count
    - Contextual: time_of_day_bin, is_returning_user, session_number
    """
    features = {}

    # Individual item scores
    for i in range(1, 10):
        features[f"phq9_item_{i}"] = phq9_responses.get(i, 0)
    for i in range(1, 8):
        features[f"gad7_item_{i}"] = gad7_responses.get(i, 0)
    for i in range(1, 11):
        raw = pss10_responses.get(i, 0)
        # Store raw (un-reverse-scored) for feature; scorer handles reversal
        features[f"pss10_item_{i}"] = raw

    # Subscale totals
    phq9_total, _ = compute_phq9_score(phq9_responses)
    gad7_total, _ = compute_gad7_score(gad7_responses)
    pss10_total, _ = compute_pss10_score(pss10_responses)

    features["phq9_total"] = phq9_total
    features["gad7_total"] = gad7_total
    features["pss10_total"] = pss10_total

    # Derived features
    phq9_vals = list(phq9_responses.values())
    gad7_vals = list(gad7_responses.values())
    pss10_vals = list(pss10_responses.values())

    features["phq9_max_item"] = max(phq9_vals) if phq9_vals else 0
    features["gad7_max_item"] = max(gad7_vals) if gad7_vals else 0
    features["phq9_severe_items"] = sum(1 for v in phq9_vals if v >= 2)
    features["gad7_severe_items"] = sum(1 for v in gad7_vals if v >= 2)
    features["phq9_variance"] = float(np.var(phq9_vals)) if phq9_vals else 0.0
    features["gad7_variance"] = float(np.var(gad7_vals)) if gad7_vals else 0.0

    # PHQ-9 item 9 = suicidal ideation (critical feature)
    features["phq9_item9_suicidal"] = phq9_responses.get(9, 0)

    # Contextual features
    if context:
        hour = context.get("hour_of_day", 12)
        if 5 <= hour < 12:
            time_bin = 0  # morning
        elif 12 <= hour < 17:
            time_bin = 1  # afternoon
        elif 17 <= hour < 21:
            time_bin = 2  # evening
        else:
            time_bin = 3  # night (insomnia proxy)
        features["time_of_day_bin"] = time_bin
        features["is_returning_user"] = int(context.get("is_returning_user", False))
        features["session_number"] = context.get("session_number", 1)
    else:
        features["time_of_day_bin"] = 1
        features["is_returning_user"] = 0
        features["session_number"] = 1

    return features


def get_feature_names() -> List[str]:
    """Return ordered list of all feature names."""
    names = []
    for i in range(1, 10): names.append(f"phq9_item_{i}")
    for i in range(1, 8):  names.append(f"gad7_item_{i}")
    for i in range(1, 11): names.append(f"pss10_item_{i}")
    names += [
        "phq9_total", "gad7_total", "pss10_total",
        "phq9_max_item", "gad7_max_item",
        "phq9_severe_items", "gad7_severe_items",
        "phq9_variance", "gad7_variance",
        "phq9_item9_suicidal",
        "time_of_day_bin", "is_returning_user", "session_number",
    ]
    return names
