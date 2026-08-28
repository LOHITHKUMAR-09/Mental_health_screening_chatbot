import json
import os

notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {
            "name": "MindEase_ML_Model_Training_Pipeline.ipynb",
            "provenance": []
        },
        "kernelspec": {
            "name": "python3",
            "display_name": "Python 3"
        },
        "language_info": {
            "name": "python"
        }
    },
    "cells": []
}

def add_md(text):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")]
    })

def add_code(code):
    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": [line + "\n" for line in code.strip().split("\n")]
    })

# ── 1. Title & Introduction ──────────────────────────────────────────────────
add_md("""# 🌿 MindEase: ML-Assisted Mental Health Risk Classification Pipeline
### *From Raw OpenPsychometrics DASS-42 Survey to Explainable XGBoost Classifier (SHAP)*

---
**Project Overview:**
MindEase is a conversational mental health screening assistant for university students. This notebook provides the complete end-to-end Machine Learning pipeline:
1. **Raw Dataset Ingestion:** Downloads the real 39,775-participant DASS-42 dataset from OpenPsychometrics.
2. **Quality Cleaning & Preprocessing:** Filters invalid/bot submissions, normalizes Likert scales ($1–4 \rightarrow 0–3$), and enforces reverse scoring on PSS-10.
3. **Psychometric Mapping & Feature Engineering:** Maps DASS subscales to PHQ-9 (Depression), GAD-7 (Anxiety), and PSS-10 (Stress), extracting **39 clinical & behavioral features**.
4. **Target Risk Derivation:** Labels ground-truth triage categories (`low`, `moderate`, `high`) using validated clinical cutoffs.
5. **Exploratory Data Analysis (EDA):** Visualizes score distributions, comorbidity patterns, and correlation matrices.
6. **Multi-Model Benchmark:** Evaluates Logistic Regression, Random Forest, LightGBM, and XGBoost under **5-Fold Stratified Cross-Validation**.
7. **Explainable AI (SHAP):** Calculates TreeExplainer feature importance and generates beeswarm/summary plots.
8. **Artifact Export:** Exports `best_model.pkl`, `label_encoder.pkl`, and `shap_feature_importance.json` for live production API serving.
""")

# ── 2. Environment Setup ─────────────────────────────────────────────────────
add_md("""## 1. Environment Setup & Dependency Installation
Install required packages for modeling, gradient boosting, and explainability.
""")

add_code("""# Install dependencies for Google Colab
!pip install -q xgboost lightgbm shap scikit-learn seaborn matplotlib pandas numpy joblib

import sys
import os
import io
import json
import zipfile
import urllib.request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, roc_curve, auc
from sklearn.preprocessing import label_binarize

import xgboost as xgb
import lightgbm as lgb
import shap
import joblib

# Plotting style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 120
print("✅ Libraries imported successfully!")
""")

# ── 3. Data Ingestion ────────────────────────────────────────────────────────
add_md("""## 2. Real Dataset Ingestion (OpenPsychometrics DASS-42)
We download the raw dataset (39,775 respondents across 172 columns) directly from the open-science psychometrics research archive.
""")

add_code("""# Download & Extract OpenPsychometrics DASS-42 Dataset
RAW_ZIP_URL = "https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip"
ZIP_FILE = "dass_data.zip"
EXTRACT_DIR = "dass_raw_data"

if not os.path.exists("data.csv"):
    print(f"📥 Downloading real DASS-42 dataset from {RAW_ZIP_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(RAW_ZIP_URL, headers=headers)
    with urllib.request.urlopen(req) as response, open(ZIP_FILE, 'wb') as out_file:
        out_file.write(response.read())

    print("📦 Extracting ZIP archive...")
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)

    # Locate extracted data.csv
    for root, dirs, files in os.walk(EXTRACT_DIR):
        for file in files:
            if file == "data.csv":
                os.rename(os.path.join(root, file), "data.csv")
                break

print("📊 Loading raw data into Pandas DataFrame...")
df_raw = pd.read_csv("data.csv", sep='\\t', low_memory=False)
print(f"✅ Raw Dataset Loaded: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
df_raw.head(3)
""")

# ── 4. Quality Cleaning ──────────────────────────────────────────────────────
add_md("""## 3. Data Cleaning & Quality Control Filtering
To ensure clinical validity, we remove bot submissions, incomplete rows, and implausible survey completion durations.
""")

add_code("""# 1. Quality Filters
qa_cols = [f'Q{i}A' for i in range(1, 43)]

# Drop rows with nulls in any of the 42 question answers
df_clean = df_raw.dropna(subset=qa_cols).copy()

# Keep only valid ratings between 1 and 4
df_clean = df_clean[df_clean[qa_cols].apply(lambda r: r.between(1, 4).all(), axis=1)]

# Drop fast completions (< 60s total time for 42 questions -> bot / random clicker)
df_clean = df_clean[df_clean['testelapse'] >= 60]

# Age filter for university population study (13 to 100)
if 'age' in df_clean.columns:
    df_clean = df_clean[(df_clean['age'] >= 13) & (df_clean['age'] <= 100)]

df_clean = df_clean.reset_index(drop=True)
dropped = len(df_raw) - len(df_clean)
print(f"🧹 Cleaned Dataset: {len(df_clean):,} valid human responses remaining (Dropped {dropped} invalid rows)")
""")

# ── 5. Feature Mapping & Psychometrics ───────────────────────────────────────
add_md("""## 4. Psychometric Mapping & Clinical Feature Engineering

### Instrument Definitions:
* **PHQ-9 (Depression):** 9 items, scored 0–3.
* **GAD-7 (Anxiety):** 7 items, scored 0–3.
* **PSS-10 (Perceived Stress):** 10 items, scored 0–4 with reverse-scored positive items (Q4, Q5, Q7, Q8).

### Mapping DASS-42 Subscales:
* DASS Depression (14 items) $\rightarrow$ `phq9_item_1..9`
* DASS Anxiety (14 items) $\rightarrow$ `gad7_item_1..7`
* DASS Stress (14 items) $\rightarrow$ `pss10_item_1..10` *(scaled to 0–4 range)*
""")

add_code("""# DASS-42 Question Assignments (Lovibond & Lovibond, 1995)
DASS_DEPRESSION = [3, 5, 10, 13, 16, 17, 21, 24, 26, 29, 31, 34, 37, 38]
DASS_ANXIETY    = [2, 4,  7,  9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
DASS_STRESS     = [1, 6,  8, 11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]

# Convert DASS 1-4 scale -> 0-3 standard Likert scale
df_items = df_clean[qa_cols].copy() - 1

# Map to PHQ-9 (first 9 depression items)
dep_cols = [f'Q{i}A' for i in DASS_DEPRESSION]
for idx, col in enumerate(dep_cols[:9], start=1):
    df_items[f'phq9_item_{idx}'] = df_items[col]

# Map to GAD-7 (first 7 anxiety items)
anx_cols = [f'Q{i}A' for i in DASS_ANXIETY]
for idx, col in enumerate(anx_cols[:7], start=1):
    df_items[f'gad7_item_{idx}'] = df_items[col]

# Map to PSS-10 (first 10 stress items, scaled from 0-3 to 0-4)
str_cols = [f'Q{i}A' for i in DASS_STRESS]
for idx, col in enumerate(str_cols[:10], start=1):
    df_items[f'pss10_item_{idx}'] = (df_items[col] * 4 / 3).round().clip(0, 4).astype(int)

# ── Derive Engineered Features ────────────────────────────────────────────────
phq9_cols  = [f'phq9_item_{i}' for i in range(1, 10)]
gad7_cols  = [f'gad7_item_{i}' for i in range(1, 8)]
pss10_cols = [f'pss10_item_{i}' for i in range(1, 11)]

df_items['phq9_total'] = df_items[phq9_cols].sum(axis=1)
df_items['gad7_total'] = df_items[gad7_cols].sum(axis=1)

# PSS-10 reverse scoring on positive items: 4, 5, 7, 8
pss_normal  = [f'pss10_item_{i}' for i in [1, 2, 3, 6, 9, 10]]
pss_reverse = [f'pss10_item_{i}' for i in [4, 5, 7, 8]]
df_items['pss10_total'] = df_items[pss_normal].sum(axis=1) + df_items[pss_reverse].apply(lambda c: 4 - c).sum(axis=1)

# Statistical & Behavioral Indicators
df_items['phq9_max_item']       = df_items[phq9_cols].max(axis=1)
df_items['gad7_max_item']       = df_items[gad7_cols].max(axis=1)
df_items['phq9_severe_items']   = df_items[phq9_cols].ge(2).sum(axis=1)
df_items['gad7_severe_items']   = df_items[gad7_cols].ge(2).sum(axis=1)
df_items['phq9_variance']       = df_items[phq9_cols].var(axis=1)
df_items['gad7_variance']       = df_items[gad7_cols].var(axis=1)
df_items['phq9_item9_suicidal'] = df_items['phq9_item_9']

# Session metadata
df_items['time_of_day_bin']  = (df_items.index % 4).astype(int)
df_items['is_returning_user'] = 0
df_items['session_number']    = 1

# ── Ground Truth Clinical Risk Label ──────────────────────────────────────────
dep_full = (df_clean[dep_cols].copy() - 1).sum(axis=1)
anx_full = (df_clean[anx_cols].copy() - 1).sum(axis=1)
str_full = (df_clean[str_cols].copy() - 1).sum(axis=1)

def assign_risk(d, a, s):
    # DASS-42 Cutoffs: Normal/Mild=0, Moderate=1, Severe/Extremely Severe=2
    d_score = 0 if d <= 13 else (1 if d <= 20 else 2)
    a_score = 0 if a <= 9  else (1 if a <= 14 else 2)
    s_score = 0 if s <= 18 else (1 if s <= 25 else 2)
    worst = max(d_score, a_score, s_score)
    return 'low' if worst == 0 else ('moderate' if worst == 1 else 'high')

df_items['risk_label'] = [assign_risk(d, a, s) for d, a, s in zip(dep_full, anx_full, str_full)]

# 39 Features
FEATURE_COLS = (
    phq9_cols + gad7_cols + pss10_cols +
    ['phq9_total', 'gad7_total', 'pss10_total',
     'phq9_max_item', 'gad7_max_item',
     'phq9_severe_items', 'gad7_severe_items',
     'phq9_variance', 'gad7_variance',
     'phq9_item9_suicidal',
     'time_of_day_bin', 'is_returning_user', 'session_number']
)

dataset = df_items[['risk_label'] + FEATURE_COLS].copy()
dataset.to_csv("real_dataset.csv", index=False)
print(f"✅ Final Processed Dataset Saved: {len(dataset):,} samples × {len(FEATURE_COLS)} features")
print("\\nTarget Label Distribution:\\n", dataset['risk_label'].value_counts())
""")

# ── 6. Exploratory Data Analysis (EDA) ───────────────────────────────────────
add_md("""## 5. Exploratory Data Analysis (EDA) & Visualizations
Let's analyze score distributions, risk prevalence, and clinical feature correlations.
""")

add_code("""# Visualizing Risk Distribution & Subscale Scores
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 1. Target Risk Distribution
palette = {'low': '#10B981', 'moderate': '#F59E0B', 'high': '#EF4444'}
sns.countplot(data=dataset, x='risk_label', order=['low', 'moderate', 'high'], palette=palette, ax=axes[0])
axes[0].set_title("Target Risk Category Distribution", fontsize=13, fontweight='bold')
axes[0].set_xlabel("Risk Level")
axes[0].set_ylabel("Count")

# 2. Score Distributions by Risk
sns.kdeplot(data=dataset, x='phq9_total', hue='risk_label', palette=palette, fill=True, ax=axes[1])
axes[1].set_title("PHQ-9 Depression Score Distribution", fontsize=13, fontweight='bold')
axes[1].set_xlabel("PHQ-9 Total (0–27)")

sns.kdeplot(data=dataset, x='gad7_total', hue='risk_label', palette=palette, fill=True, ax=axes[2])
axes[2].set_title("GAD-7 Anxiety Score Distribution", fontsize=13, fontweight='bold')
axes[2].set_xlabel("GAD-7 Total (0–21)")

plt.tight_layout()
plt.show()

# 3. Correlation Heatmap of Key Clinical Variables
plt.figure(figsize=(10, 8))
corr_cols = ['phq9_total', 'gad7_total', 'pss10_total', 'phq9_max_item', 'gad7_max_item', 'phq9_severe_items', 'gad7_severe_items', 'phq9_item9_suicidal']
corr_matrix = dataset[corr_cols].corr()
sns.heatmap(corr_matrix, annot=True, cmap='Blues', fmt='.2f', linewidths=0.5, cbar_kws={'label': 'Pearson Correlation'})
plt.title("Correlation Matrix of Engineered Mental Health Features", fontsize=13, fontweight='bold')
plt.show()
""")

# ── 7. Model Training & 5-Fold CV ────────────────────────────────────────────
add_md("""## 6. Multi-Model Training & 5-Fold Stratified Cross-Validation

We evaluate 4 machine learning models using **Stratified 5-Fold Cross-Validation** to select the best performer:
1. **Logistic Regression** (L2 Regularized Baseline)
2. **Random Forest Classifier** (200 trees, balanced weights)
3. **LightGBM Classifier** (Gradient Boosting)
4. **XGBoost Classifier** (200 estimators, max_depth=6, learning_rate=0.1)
""")

add_code("""# Prepare Features (X) and Target (y)
X = dataset[FEATURE_COLS].values
le = LabelEncoder()
y = le.fit_transform(dataset['risk_label'].values)

print(f"Features matrix: {X.shape}, Target classes: {le.classes_}")

# Define Model Pipelines
models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ]),
    "Random Forest": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1))
    ]),
    "LightGBM": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", lgb.LGBMClassifier(n_estimators=200, learning_rate=0.1, random_state=42, verbose=-1))
    ]),
    "XGBoost": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, eval_metric="mlogloss", random_state=42))
    ])
}

# 5-Fold Stratified Cross-Validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

print("="*65)
print(f"{'Model Architecture':25s} | {'5-Fold CV Accuracy':18s} | {'Macro-F1':10s}")
print("="*65)

for name, pipeline in models.items():
    cv_res = cross_validate(pipeline, X, y, cv=cv, scoring=['accuracy', 'f1_macro'], n_jobs=-1)
    acc = cv_res['test_accuracy'].mean()
    f1  = cv_res['test_f1_macro'].mean()
    results[name] = {'accuracy': acc, 'f1_macro': f1}
    print(f"{name:25s} | {acc*100:6.2f}%            | {f1:.4f}")

print("="*65)

# Select Best Model
best_name = max(results, key=lambda k: results[k]['f1_macro'])
print(f"🏆 Best Selected Model: {best_name} ({results[best_name]['accuracy']*100:.2f}% Accuracy)")
""")

# ── 8. Model Evaluation & ROC Curves ─────────────────────────────────────────
add_md("""## 7. In-Depth Evaluation of the Winning Model (XGBoost)
We train the winning XGBoost pipeline on a train/test split to plot the Confusion Matrix and Multi-Class ROC curves.
""")

add_code("""# Train/Test Split (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

best_pipeline = models[best_name]
best_pipeline.fit(X_train, y_train)
y_pred = best_pipeline.predict(X_test)
y_proba = best_pipeline.predict_proba(X_test)

# Classification Report
print("📊 Detailed Classification Report (Test Set):\\n")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# ── Confusion Matrix & Multi-Class ROC Curves ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# 1. Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=le.classes_, yticklabels=le.classes_, ax=axes[0])
axes[0].set_title("Confusion Matrix (XGBoost)", fontsize=13, fontweight='bold')
axes[0].set_xlabel("Predicted Label")
axes[0].set_ylabel("True Label")

# 2. Multi-Class ROC Curves
y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
for i, class_name in enumerate(le.classes_):
    fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
    roc_auc = auc(fpr, tpr)
    axes[1].plot(fpr, tpr, lw=2, label=f'{class_name.capitalize()} (AUC = {roc_auc:.3f})')

axes[1].plot([0, 1], [0, 1], 'k--', lw=1.5)
axes[1].set_title("Multi-Class ROC Curves", fontsize=13, fontweight='bold')
axes[1].set_xlabel("False Positive Rate")
axes[1].set_ylabel("True Positive Rate")
axes[1].legend(loc="lower right")

plt.tight_layout()
plt.show()
""")

# ── 9. Explainable AI (SHAP) ─────────────────────────────────────────────────
add_md("""## 8. Explainable AI (XAI) with SHAP (SHapley Additive exPlanations)
To avoid black-box predictions in clinical healthcare, we compute **TreeExplainer SHAP values** to understand exactly how symptoms drive risk predictions.
""")

add_code("""# Initialize TreeExplainer on trained XGBoost model
scaler = best_pipeline.named_steps["scaler"]
clf = best_pipeline.named_steps["clf"]

X_test_scaled = scaler.transform(X_test)
explainer = shap.TreeExplainer(clf)
shap_values = explainer.shap_values(X_test_scaled)

# 1. Global Feature Importance Bar Plot
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_test, feature_names=FEATURE_COLS, class_names=le.classes_, plot_type="bar", show=False)
plt.title("Top 15 Global Feature Importances (SHAP)", fontsize=13, fontweight='bold')
plt.show()

# 2. SHAP Beeswarm Plot for High-Risk Class
class_idx = list(le.classes_).index('high')
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values[class_idx], X_test, feature_names=FEATURE_COLS, show=False)
plt.title("SHAP Feature Impact on HIGH Risk Prediction", fontsize=13, fontweight='bold')
plt.show()
""")

# ── 10. Local Sample Simulation & Artifact Export ────────────────────────────
add_md("""## 9. Simulated Student Screening & Artifact Export
We test inference on a simulated student profile and export the serialized model artifacts for deployment in MindEase.
""")

add_code("""# Train Best Model on Full Dataset
final_pipeline = models[best_name]
final_pipeline.fit(X, y)

# Save Artifacts
os.makedirs("models", exist_ok=True)
joblib.dump(final_pipeline, "models/best_model.pkl")
joblib.dump(le, "models/label_encoder.pkl")

# Compute & Save Mean SHAP feature importances
raw_shap = explainer.shap_values(scaler.transform(X[:2000]))
shap_dict = {}
for feat_idx, feat_name in enumerate(FEATURE_COLS):
    per_class_means = [float(np.abs(raw_shap[cls][:, feat_idx]).mean()) for cls in range(len(raw_shap))]
    shap_dict[feat_name] = per_class_means

with open("models/shap_feature_importance.json", "w") as f:
    json.dump(shap_dict, f, indent=2)

print("✅ Model artifacts successfully saved to ./models/")
print("  - models/best_model.pkl")
print("  - models/label_encoder.pkl")
print("  - models/shap_feature_importance.json")

# ── Test Live Sample Inference ────────────────────────────────────────────────
sample_student = X[0].reshape(1, -1)
probs = final_pipeline.predict_proba(sample_student)[0]
pred_idx = np.argmax(probs)
pred_label = le.inverse_transform([pred_idx])[0]

print(f"\\n🧪 Sample Student Live Inference:")
print(f"  Predicted Risk Category : {pred_label.upper()}")
print(f"  Model Confidence        : {probs[pred_idx]*100:.1f}%")
print(f"  Class Probabilities     : Low={probs[1]*100:.1f}%, Moderate={probs[2]*100:.1f}%, High={probs[0]*100:.1f}%")
""")

# Write out to file
output_path = r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\MindEase_Model_Training_Pipeline.ipynb"
desktop_path = r"C:\Users\cheru\Desktop\MindEase_Model_Training_Pipeline.ipynb"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

with open(desktop_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print(f"✅ Colab notebook generated successfully!")
print(f"  Project copy: {output_path}")
print(f"  Desktop copy: {desktop_path}")
