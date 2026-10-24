"""
ML Training Pipeline — MindEase Mental Health Risk Classifier
Trains and evaluates multiple models, saves best model + SHAP values.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
import shap

# Paths
BASE = Path(__file__).parent
# Real dataset: 39,648 participants from OpenPsychometrics DASS-42 survey
# Mapped from DASS-42 subscales to PHQ-9/GAD-7/PSS-10 feature schema
REAL_DATA_PATH      = BASE / "data" / "processed" / "real_dataset.csv"
SYNTHETIC_DATA_PATH = BASE / "data" / "synthetic" / "synthetic_dataset.csv"
DATA_PATH = REAL_DATA_PATH if REAL_DATA_PATH.exists() else SYNTHETIC_DATA_PATH
MODELS_DIR = BASE / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ── Step 1: Load data ─────────────────────────────────────────────
print(f"[Dataset] Using: {DATA_PATH.name}")

print(f"Loading data from {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"Dataset shape: {df.shape}")
print(f"Risk distribution:\n{df['risk_label'].value_counts()}")

# ── Step 2: Feature preparation ───────────────────────────────────
FEATURE_COLS = (
    [f"phq9_item_{i}" for i in range(1, 10)] +
    [f"gad7_item_{i}" for i in range(1, 8)] +
    [f"pss10_item_{i}" for i in range(1, 11)] +
    ["phq9_total", "gad7_total", "pss10_total",
     "phq9_max_item", "gad7_max_item",
     "phq9_severe_items", "gad7_severe_items",
     "phq9_variance", "gad7_variance",
     "phq9_item9_suicidal",
     "time_of_day_bin", "is_returning_user", "session_number"]
)

# Keep only columns that exist
FEATURE_COLS = [c for c in FEATURE_COLS if c in df.columns]
X = df[FEATURE_COLS].values
y_raw = df["risk_label"].values

le = LabelEncoder()
y = le.fit_transform(y_raw)
print(f"Classes: {le.classes_}")

# Save label encoder
joblib.dump(le, MODELS_DIR / "label_encoder.pkl")

# ── Step 3: Define models ──────────────────────────────────────────
models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ]),
    "Random Forest": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)),
    ]),
    "LightGBM": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", lgb.LGBMClassifier(n_estimators=200, learning_rate=0.1, random_state=42, verbose=-1)),
    ]),
    "XGBoost": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", xgb.XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            eval_metric="mlogloss",
            random_state=42,
        )),
    ]),
}

# ── Step 4: Stratified 5-fold cross-validation ────────────────────
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

print("\n" + "="*60)
print("MODEL EVALUATION (5-Fold Stratified Cross-Validation)")
print("="*60)

for name, pipeline in models.items():
    cv_results = cross_validate(
        pipeline, X, y, cv=cv,
        scoring=["accuracy", "f1_macro"],
        return_train_score=True,
    )
    acc = cv_results["test_accuracy"].mean()
    f1  = cv_results["test_f1_macro"].mean()
    results[name] = {"accuracy": acc, "f1_macro": f1}
    print(f"{name:25s}  Accuracy={acc*100:.2f}%  F1-Macro={f1:.4f}")

# ── Step 5: Train best model on full data ─────────────────────────
best_name = max(results, key=lambda k: results[k]["f1_macro"])
print(f"\n[BEST] Best model selected: {best_name} ({results[best_name]['accuracy']*100:.2f}% Accuracy)")

best_pipeline = models[best_name]
best_pipeline.fit(X, y)

joblib.dump(best_pipeline, MODELS_DIR / "best_model.pkl")
print(f"Saved best model -> {MODELS_DIR / 'best_model.pkl'}")

# ── Step 6: Full classification report ────────────────────────────
y_pred = best_pipeline.predict(X)
print("\n--- Classification Report (Training Set) ---")
print(classification_report(y, y_pred, target_names=le.classes_))

# ── Step 7: SHAP analysis on best model ───────────────────────────
print(f"\nComputing SHAP values on best model ({best_name})...")
X_scaled = best_pipeline.named_steps["scaler"].transform(X)
explainer = shap.TreeExplainer(best_pipeline.named_steps["clf"])
raw_shap = explainer.shap_values(X_scaled)

# Feature importance from SHAP (mean absolute SHAP values per class, averaged)
raw_shap = explainer.shap_values(X_scaled)
# raw_shap can be: list of arrays [n_samples, n_features] x n_classes, or 3D array
if isinstance(raw_shap, list):
    # list of 2D arrays -> stack to 3D [n_classes, n_samples, n_features]
    shap_3d = np.array(raw_shap)  # shape: (n_classes, n_samples, n_features)
    mean_shap_per_class = np.abs(shap_3d).mean(axis=1)  # (n_classes, n_features)
    mean_shap = mean_shap_per_class.mean(axis=0)        # (n_features,)
elif raw_shap.ndim == 3:
    # 3D array [n_samples, n_features, n_classes]
    mean_shap = np.abs(raw_shap).mean(axis=0).mean(axis=1)  # (n_features,)
else:
    mean_shap = np.abs(raw_shap).mean(axis=0)

# Store per-class SHAP lists for the predictor (one list per feature)
if isinstance(raw_shap, list):
    shap_per_class_dict = {}
    for feat_idx, feat_name in enumerate(FEATURE_COLS):
        per_class_means = [float(np.abs(raw_shap[cls][:, feat_idx]).mean()) for cls in range(len(raw_shap))]
        shap_per_class_dict[feat_name] = per_class_means
else:
    shap_per_class_dict = {feat: [float(mean_shap[i])] * 3 for i, feat in enumerate(FEATURE_COLS)}

feature_importance = dict(zip(FEATURE_COLS, mean_shap.tolist()))
sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

print("\n--- Top 10 Most Important Features (SHAP) ---")
for feat, val in list(sorted_importance.items())[:10]:
    print(f"  {feat:30s}  {val:.4f}")

# Save SHAP feature importance (per-class lists — matches predictor.py format)
with open(MODELS_DIR / "shap_feature_importance.json", "w") as f:
    json.dump(shap_per_class_dict, f, indent=2)

# Save evaluation results
eval_results = {
    "models": results,
    "best_model": best_name,
    "classes": le.classes_.tolist(),
    "feature_count": len(FEATURE_COLS),
    "features": FEATURE_COLS,
}
with open(MODELS_DIR / "evaluation_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

print(f"\nAll artifacts saved to: {MODELS_DIR}")
print("Pipeline complete!")
