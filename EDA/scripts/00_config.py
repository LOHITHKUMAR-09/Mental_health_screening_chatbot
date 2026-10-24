"""
00_config.py
============
Central configuration for all EDA scripts.

REASON: A single config file prevents hardcoded paths scattered across scripts,
makes the project portable, and provides one place to update the data path
or output directories when the project structure changes.
"""

import os

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # EDA/
DATA_PATH   = os.path.join(BASE_DIR, os.pardir,
              "ml", "data", "raw", "DASS_data_21.02.19", "data.csv")
DATA_PATH   = os.path.normpath(DATA_PATH)
OUT_FIG     = os.path.join(BASE_DIR, "outputs", "figures")
OUT_REP     = os.path.join(BASE_DIR, "outputs", "reports")

# ── DASS-42 subscale question mapping (1-indexed) ────────────────────────────
# REASON: The DASS-42 has 42 items mapped to 3 subscales.
# Each subscale uses 14 items; to align with DASS-21 norms the raw sum is
# multiplied by 2.  Mapping defined once here so all scripts stay consistent.
DEPRESSION_QS = [3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42]
ANXIETY_QS    = [2, 4, 7,  9,  15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
STRESS_QS     = [1, 6, 8,  11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]

# ── Severity thresholds (DASS-21 scale) ──────────────────────────────────────
# Source: Lovibond & Lovibond (1995)
SEVERITY = {
    "Depression": [(0, 9, "Normal"), (10, 13, "Mild"), (14, 20, "Moderate"),
                   (21, 27, "Severe"), (28, 999, "Extremely Severe")],
    "Anxiety":    [(0, 7, "Normal"), (8,  9,  "Mild"), (10, 14, "Moderate"),
                   (15, 19, "Severe"), (20, 999, "Extremely Severe")],
    "Stress":     [(0, 14, "Normal"), (15, 18, "Mild"), (19, 25, "Moderate"),
                   (26, 33, "Severe"), (34, 999, "Extremely Severe")],
}

# ── Demographic label maps ────────────────────────────────────────────────────
GENDER_MAP    = {"1": "Male", "2": "Female", "3": "Other", "0": "Unknown"}
EDUCATION_MAP = {"0": "Unknown", "1": "< High School", "2": "High School",
                 "3": "University", "4": "Graduate"}
URBAN_MAP     = {"1": "Rural", "2": "Suburban", "3": "Urban", "0": "Unknown"}
HAND_MAP      = {"1": "Right", "2": "Left", "3": "Both", "0": "Unknown"}
ENGNAT_MAP    = {"1": "Yes", "2": "No", "0": "Unknown"}
MARRIED_MAP   = {"1": "Never married", "2": "Married", "3": "Previously married", "0": "Unknown"}
ORIENTATION_MAP = {"1": "Heterosexual", "2": "Bisexual", "3": "Homosexual",
                   "4": "Asexual", "5": "Other", "0": "Unknown"}

# ── VCL fake words (for validity filtering) ───────────────────────────────────
VCL_FAKE = ["VCL6", "VCL9", "VCL12"]

# ── Plot style ───────────────────────────────────────────────────────────────
PALETTE = {
    "Normal":           "#2ecc71",
    "Mild":             "#f1c40f",
    "Moderate":         "#e67e22",
    "Severe":           "#e74c3c",
    "Extremely Severe": "#8e1010",
    "Depression":       "#3498db",
    "Anxiety":          "#e74c3c",
    "Stress":           "#f39c12",
}
FIG_DPI  = 150
FIG_SIZE = (14, 7)
