"""
ML Risk Prediction Service.
Loads trained Random Forest pipeline and generates 39 features matching
exactly what the model was trained on in ml/train_models.py.
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH   = BASE_DIR / "ml" / "models" / "best_model.pkl"
ENCODER_PATH = BASE_DIR / "ml" / "models" / "label_encoder.pkl"
SHAP_PATH    = BASE_DIR / "ml" / "models" / "shap_feature_importance.json"

# PSS-10 reverse-scored items (1-indexed): 4, 5, 7, 8
PSS10_REVERSE = {4, 5, 7, 8}

# Exact feature order the model was trained on (39 features)
FEATURE_COLS = (
    [f"phq9_item_{i}" for i in range(1, 10)] +      # 9
    [f"gad7_item_{i}" for i in range(1, 8)] +        # 7
    [f"pss10_item_{i}" for i in range(1, 11)] +      # 10
    [
        "phq9_total", "gad7_total", "pss10_total",   # 3 totals
        "phq9_max_item", "gad7_max_item",            # 2 max
        "phq9_severe_items", "gad7_severe_items",    # 2 severe counts
        "phq9_variance", "gad7_variance",            # 2 variances
        "phq9_item9_suicidal",                       # 1 crisis flag
        "time_of_day_bin", "is_returning_user", "session_number",  # 3 meta
    ]
)   # total = 9 + 7 + 10 + 13 = 39


class MLPredictor:
    def __init__(self):
        self.model = None
        self.encoder = None
        self.shap_importance = {}
        self._load()

    def _load(self):
        try:
            self.model   = joblib.load(MODEL_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
            if SHAP_PATH.exists():
                with open(SHAP_PATH) as f:
                    self.shap_importance = json.load(f)
            print(f"[MLPredictor] Loaded ({len(FEATURE_COLS)} features)")
        except Exception as e:
            print(f"[MLPredictor] Warning: {e}")

    def extract_features(self, all_responses: Dict[str, Dict[int, int]]) -> pd.DataFrame:
        phq9  = all_responses.get("phq9",  {})
        gad7  = all_responses.get("gad7",  {})
        pss10 = all_responses.get("pss10", {})

        row: Dict[str, float] = {}

        # Raw PHQ-9 items
        phq9_vals = []
        for i in range(1, 10):
            v = phq9.get(i, 0)
            row[f"phq9_item_{i}"] = v
            phq9_vals.append(v)

        # Raw GAD-7 items
        gad7_vals = []
        for i in range(1, 8):
            v = gad7.get(i, 0)
            row[f"gad7_item_{i}"] = v
            gad7_vals.append(v)

        # Raw PSS-10 items (stored as-is, NOT reverse-scored yet)
        pss10_raw = []
        for i in range(1, 11):
            v = pss10.get(i, 0)
            row[f"pss10_item_{i}"] = v
            pss10_raw.append((i, v))

        # Totals
        phq9_total  = sum(phq9_vals)
        gad7_total  = sum(gad7_vals)
        pss10_total = sum(
            (4 - v) if i in PSS10_REVERSE else v
            for i, v in pss10_raw
        )

        row["phq9_total"]  = phq9_total
        row["gad7_total"]  = gad7_total
        row["pss10_total"] = pss10_total

        # Derived features
        row["phq9_max_item"]      = max(phq9_vals) if phq9_vals else 0
        row["gad7_max_item"]      = max(gad7_vals) if gad7_vals else 0
        row["phq9_severe_items"]  = sum(1 for v in phq9_vals if v >= 2)
        row["gad7_severe_items"]  = sum(1 for v in gad7_vals if v >= 2)
        row["phq9_variance"]      = float(np.var(phq9_vals)) if phq9_vals else 0.0
        row["gad7_variance"]      = float(np.var(gad7_vals)) if gad7_vals else 0.0
        row["phq9_item9_suicidal"] = phq9.get(9, 0)

        # Contextual metadata (use neutral defaults for single-session)
        row["time_of_day_bin"]  = 1   # daytime
        row["is_returning_user"] = 0
        row["session_number"]   = 1

        return pd.DataFrame([row])[FEATURE_COLS].astype(float)

    def predict(self, all_responses: Dict[str, Dict[int, int]]) -> Tuple[str, float, Dict[str, float]]:
        if self.model is None or self.encoder is None:
            return ("moderate", 0.75, {})

        features_df = self.extract_features(all_responses)
        probs   = self.model.predict_proba(features_df.values)[0]
        idx     = int(np.argmax(probs))
        conf    = float(probs[idx])
        label   = str(self.encoder.inverse_transform([idx])[0])

        top_shap: Dict[str, float] = {}
        if self.shap_importance:
            # shap_importance values can be lists (per-class) — take the mean
            averaged = {}
            for k, v in self.shap_importance.items():
                if isinstance(v, list):
                    averaged[k] = float(sum(v) / len(v))
                else:
                    averaged[k] = float(v)
            top_shap = dict(
                sorted(averaged.items(), key=lambda x: x[1], reverse=True)[:5]
            )
        return label, round(conf, 3), top_shap


ml_predictor = MLPredictor()


