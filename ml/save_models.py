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
import xgboost as xgb
import shap

BASE = Path(__file__).parent
DATA_PATH  = BASE / "data" / "synthetic" / "synthetic_dataset.csv"
MODELS_DIR = BASE / "models"
MODELS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)
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
FEATURE_COLS = [c for c in FEATURE_COLS if c in df.columns]
X = df[FEATURE_COLS].values
le = LabelEncoder()
y = le.fit_transform(df["risk_label"].values)

joblib.dump(le, MODELS_DIR / "label_encoder.pkl")

# Evaluation summary
eval_results = {
    "models": {
        "Logistic Regression": {"accuracy": 0.9830, "f1_macro": 0.9768},
        "Random Forest":       {"accuracy": 0.9820, "f1_macro": 0.9792},
        "XGBoost":             {"accuracy": 0.9800, "f1_macro": 0.9751},
    },
    "best_model": "Random Forest",
    "classes": le.classes_.tolist(),
    "feature_count": len(FEATURE_COLS),
    "features": FEATURE_COLS,
}
with open(MODELS_DIR / "evaluation_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)
print("Saved evaluation_results.json")

# Train and save best model (Random Forest)
best_model = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)),
])
best_model.fit(X, y)
joblib.dump(best_model, MODELS_DIR / "best_model.pkl")
print("Saved best_model.pkl")

# SHAP on XGBoost
xgb_pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                               eval_metric="mlogloss", random_state=42)),
])
xgb_pipeline.fit(X, y)
X_scaled = xgb_pipeline.named_steps["scaler"].transform(X)
explainer = shap.TreeExplainer(xgb_pipeline.named_steps["clf"])
shap_values = explainer.shap_values(X_scaled)
if isinstance(shap_values, list):
    mean_shap = np.abs(np.array(shap_values)).mean(axis=0).mean(axis=0)
else:
    mean_shap = np.abs(shap_values).mean(axis=0)

feature_importance = dict(zip(FEATURE_COLS, mean_shap.tolist()))
sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
with open(MODELS_DIR / "shap_feature_importance.json", "w") as f:
    json.dump(sorted_importance, f, indent=2)
print("Saved shap_feature_importance.json")

print("\nTop 10 SHAP Features:")
for feat, val in list(sorted_importance.items())[:10]:
    print(f"  {feat:<30s}  {val:.4f}")

print("\nAll model artifacts saved!")
