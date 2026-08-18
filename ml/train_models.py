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
import shap

# Paths
BASE = Path(__file__).parent
DATA_PATH  = BASE / "data" / "synthetic" / "synthetic_dataset.csv"
MODELS_DIR = BASE / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ── Step 1: Generate data if not exists ──────────────────────────
if not DATA_PATH.exists():
    print("Generating synthetic dataset...")
    exec(open(BASE / "data" / "generate_synthetic.py").read())

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
scaler = StandardScaler()

models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ]),
    "Random Forest": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)),
    ]),
    "XGBoost": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", xgb.XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            use_label_encoder=False, eval_metric="mlogloss",
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
    print(f"{name:25s}  Accuracy={acc:.4f}  F1-Macro={f1:.4f}")

# ── Step 5: Train best model on full data ─────────────────────────
best_name = max(results, key=lambda k: results[k]["f1_macro"])
print(f"\nBest model: {best_name}")

best_pipeline = models[best_name]
best_pipeline.fit(X, y)

# Save best model
joblib.dump(best_pipeline, MODELS_DIR / "best_model.pkl")
print(f"Saved best model → {MODELS_DIR / 'best_model.pkl'}")

# ── Step 6: Full classification report ────────────────────────────
y_pred = best_pipeline.predict(X)
print("\n--- Classification Report (Training Set) ---")
print(classification_report(y, y_pred, target_names=le.classes_))

# ── Step 7: SHAP analysis on XGBoost ──────────────────────────────
print("\nComputing SHAP values...")
xgb_pipeline = models["XGBoost"]
xgb_pipeline.fit(X, y)

# SHAP explainer on the raw XGBoost classifier
X_scaled = xgb_pipeline.named_steps["scaler"].transform(X)
explainer = shap.TreeExplainer(xgb_pipeline.named_steps["clf"])
shap_values = explainer.shap_values(X_scaled)

# Feature importance from SHAP (mean absolute SHAP values)
if isinstance(shap_values, list):
    mean_shap = np.abs(np.array(shap_values)).mean(axis=0).mean(axis=0)
else:
    mean_shap = np.abs(shap_values).mean(axis=0)

feature_importance = dict(zip(FEATURE_COLS, mean_shap.tolist()))
sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

print("\n--- Top 10 Most Important Features (SHAP) ---")
for feat, val in list(sorted_importance.items())[:10]:
    bar = "█" * int(val * 20)
    print(f"  {feat:30s}  {val:.4f}  {bar}")

# Save SHAP feature importance
with open(MODELS_DIR / "shap_feature_importance.json", "w") as f:
    json.dump(sorted_importance, f, indent=2)

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
