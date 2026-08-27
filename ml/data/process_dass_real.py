"""
DASS-42 -> MindEase Feature Mapping Pipeline
============================================
Converts real 39,775-participant DASS-42 dataset into the 39-feature schema
expected by the MindEase ML model, then saves to ml/data/processed/real_dataset.csv

Mapping:
  DASS Depression (14 items) -> PHQ-9 proxy  (first 9 items used, 0-3 scale)
  DASS Anxiety    (14 items) -> GAD-7 proxy  (first 7 items used, 0-3 scale)
  DASS Stress     (14 items) -> PSS-10 proxy (first 10 items, scaled to 0-4)
  Risk label from DASS-42 clinical severity cutoffs -> low/moderate/high
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_CSV    = Path(__file__).parent / "raw" / "data.csv"
OUTPUT_CSV = Path(__file__).parent / "processed" / "real_dataset.csv"
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# Official DASS-42 subscale question numbers (Lovibond & Lovibond, 1995)
DASS_DEPRESSION = [3, 5, 10, 13, 16, 17, 21, 24, 26, 29, 31, 34, 37, 38]
DASS_ANXIETY    = [2, 4,  7,  9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
DASS_STRESS     = [1, 6,  8, 11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]

def dass_dep_severity(score):
    if score <= 9:  return "normal"
    if score <= 13: return "mild"
    if score <= 20: return "moderate"
    if score <= 27: return "severe"
    return "extremely_severe"

def dass_anx_severity(score):
    if score <= 7:  return "normal"
    if score <= 9:  return "mild"
    if score <= 14: return "moderate"
    if score <= 19: return "severe"
    return "extremely_severe"

def dass_str_severity(score):
    if score <= 14: return "normal"
    if score <= 18: return "mild"
    if score <= 25: return "moderate"
    if score <= 33: return "severe"
    return "extremely_severe"

def composite_risk(dep_sev, anx_sev, str_sev):
    ORDER = {"normal": 0, "mild": 1, "moderate": 2, "severe": 3, "extremely_severe": 4}
    worst = max(ORDER[dep_sev], ORDER[anx_sev], ORDER[str_sev])
    if worst <= 1: return "low"
    if worst <= 3: return "moderate"
    return "high"

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading real DASS-42 dataset...")
df = pd.read_csv(RAW_CSV, sep='\t', low_memory=False)
print(f"  Raw rows: {len(df)}")

# ── Quality Filters ───────────────────────────────────────────────────────────
qa_cols = [f'Q{i}A' for i in range(1, 43)]
df = df.dropna(subset=qa_cols)
df = df[df[qa_cols].apply(lambda r: r.between(1, 4).all(), axis=1)]
df = df[df['testelapse'] >= 60]
if 'age' in df.columns:
    df = df[(df['age'] >= 13) & (df['age'] <= 100)]
df = df.reset_index(drop=True)
print(f"  After quality filters: {len(df)} rows remaining")

# ── Step 1: Convert DASS 1-4 -> 0-3 ──────────────────────────────────────────
df_q = df[qa_cols].copy() - 1

# ── Step 2: Depression -> PHQ-9 (first 9 of 14 DASS depression items) ─────────
dep_qa = [f'Q{i}A' for i in DASS_DEPRESSION]
for phq_idx, col in enumerate(dep_qa[:9], start=1):
    df_q[f'phq9_item_{phq_idx}'] = df_q[col]

# ── Step 3: Anxiety -> GAD-7 (first 7 of 14 DASS anxiety items) ───────────────
anx_qa = [f'Q{i}A' for i in DASS_ANXIETY]
for gad_idx, col in enumerate(anx_qa[:7], start=1):
    df_q[f'gad7_item_{gad_idx}'] = df_q[col]

# ── Step 4: Stress -> PSS-10 (first 10 of 14 DASS stress items, scaled 0-4) ───
str_qa = [f'Q{i}A' for i in DASS_STRESS]
for pss_idx, col in enumerate(str_qa[:10], start=1):
    scaled = (df_q[col] * 4 / 3).round().clip(0, 4).astype(int)
    df_q[f'pss10_item_{pss_idx}'] = scaled

# ── Step 5: Derive 13 engineered features ────────────────────────────────────
phq9_cols  = [f'phq9_item_{i}' for i in range(1, 10)]
gad7_cols  = [f'gad7_item_{i}' for i in range(1, 8)]
pss10_cols = [f'pss10_item_{i}' for i in range(1, 11)]

df_q['phq9_total'] = df_q[phq9_cols].sum(axis=1)
df_q['gad7_total'] = df_q[gad7_cols].sum(axis=1)

# PSS-10 reverse scoring on items 4, 5, 7, 8 (matches train_models.py)
pss_normal  = [f'pss10_item_{i}' for i in [1, 2, 3, 6, 9, 10]]
pss_reverse = [f'pss10_item_{i}' for i in [4, 5, 7, 8]]
df_q['pss10_total'] = (
    df_q[pss_normal].sum(axis=1) +
    df_q[pss_reverse].apply(lambda col: 4 - col).sum(axis=1)
)

df_q['phq9_max_item']       = df_q[phq9_cols].max(axis=1)
df_q['gad7_max_item']       = df_q[gad7_cols].max(axis=1)
df_q['phq9_severe_items']   = df_q[phq9_cols].ge(2).sum(axis=1)
df_q['gad7_severe_items']   = df_q[gad7_cols].ge(2).sum(axis=1)
df_q['phq9_variance']       = df_q[phq9_cols].var(axis=1)
df_q['gad7_variance']       = df_q[gad7_cols].var(axis=1)
df_q['phq9_item9_suicidal'] = df_q['phq9_item_9']
df_q['time_of_day_bin']     = (df_q.index % 4).astype(int)
df_q['is_returning_user']   = 0
df_q['session_number']      = 1

# ── Step 6: Assign composite risk label from full 14-item DASS scores ──────────
dep_full = (df[[f'Q{i}A' for i in DASS_DEPRESSION]].copy() - 1).sum(axis=1)
anx_full = (df[[f'Q{i}A' for i in DASS_ANXIETY]].copy() - 1).sum(axis=1)
str_full = (df[[f'Q{i}A' for i in DASS_STRESS]].copy() - 1).sum(axis=1)

df_q['risk_label'] = [
    composite_risk(
        dass_dep_severity(d),
        dass_anx_severity(a),
        dass_str_severity(s)
    )
    for d, a, s in zip(dep_full, anx_full, str_full)
]

# ── Step 7: Final column order matches train_models.py exactly ────────────────
FEATURE_COLS = (
    [f'phq9_item_{i}' for i in range(1, 10)] +
    [f'gad7_item_{i}' for i in range(1, 8)] +
    [f'pss10_item_{i}' for i in range(1, 11)] +
    ['phq9_total', 'gad7_total', 'pss10_total',
     'phq9_max_item', 'gad7_max_item',
     'phq9_severe_items', 'gad7_severe_items',
     'phq9_variance', 'gad7_variance',
     'phq9_item9_suicidal',
     'time_of_day_bin', 'is_returning_user', 'session_number']
)

final_df = df_q[['risk_label'] + FEATURE_COLS].copy()

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  DASS-42 -> MindEase Feature Mapping Complete")
print(f"{'='*55}")
print(f"  Output rows  : {len(final_df):,}")
print(f"  Feature cols : {len(FEATURE_COLS)} (matches model exactly)")
print(f"\n  Risk label distribution:")
vc = final_df['risk_label'].value_counts()
for label, count in vc.items():
    pct = count / len(final_df) * 100
    print(f"    {label:10s}: {count:6,}  ({pct:.1f}%)")
print(f"\n  Score ranges after mapping:")
print(f"    phq9_total  : {final_df['phq9_total'].min():.0f} - {final_df['phq9_total'].max():.0f}  (PHQ-9 range 0-27)")
print(f"    gad7_total  : {final_df['gad7_total'].min():.0f} - {final_df['gad7_total'].max():.0f}  (GAD-7 range 0-21)")
print(f"    pss10_total : {final_df['pss10_total'].min():.0f} - {final_df['pss10_total'].max():.0f}  (PSS-10 range 0-40)")
print(f"\n  Saved to: {OUTPUT_CSV}")

final_df.to_csv(OUTPUT_CSV, index=False)
print("  Done.")
