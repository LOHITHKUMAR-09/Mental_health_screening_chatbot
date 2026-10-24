"""
07_class_balance.py
===================
Step 7 – Class Balance & ML Readiness Assessment

PURPOSE & REASON:
  For supervised ML we must treat DASS severity as the label.
  This script:
    1. Evaluates the class balance for each severity level across all three
       subscales — severe class imbalance will require SMOTE/class-weight
       strategies during training.
    2. Tests different label strategies: 5-class (all severity levels) vs.
       binary (Normal vs. Elevated) vs. 3-class (Normal / Moderate / Severe+).
    3. Computes the effective number of samples per class after data quality
       filtering (valid age + VCL pass + non-duplicate).
    4. Summarises which features have the most predictive signal (from script 06).

OUTPUT:
  outputs/figures/07_class_balance_5class.png
  outputs/figures/07_class_balance_binary.png
  outputs/figures/07_class_balance_3class.png
  outputs/figures/07_sample_funnel.png
  outputs/reports/ml_readiness_report.txt
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config_loader import *   # noqa

import pandas as pd
import numpy  as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

print("[07] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# ── Compute scores ─────────────────────────────────────────────────────────────
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    return (df[cols].apply(pd.to_numeric, errors="coerce") - 1).sum(axis=1) * 2

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

severity_order = ["Normal","Mild","Moderate","Severe","Extremely Severe"]
severity_colors = [PALETTE[s] for s in severity_order]

def classify_severity(score, bands):
    for lo, hi, label in bands:
        if lo <= score <= hi:
            return label
    return "Unknown"

for subscale, bands in SEVERITY.items():
    df[f"{subscale}_5cls"] = df[subscale].apply(classify_severity, bands=bands)

# ── Binary: Normal vs Elevated ─────────────────────────────────────────────────
for subscale in ["Depression","Anxiety","Stress"]:
    df[f"{subscale}_binary"] = df[f"{subscale}_5cls"].apply(
        lambda x: "Normal" if x == "Normal" else "Elevated")

# ── 3-class: Normal / Moderate / Severe+ ──────────────────────────────────────
def to_3class(sev):
    if sev == "Normal":   return "Normal"
    if sev in ["Mild","Moderate"]: return "Mild-Moderate"
    return "Severe+"

for subscale in ["Depression","Anxiety","Stress"]:
    df[f"{subscale}_3cls"] = df[f"{subscale}_5cls"].apply(to_3class)

lines = []
def log(m=""):
    print(m); lines.append(m)

log("=" * 60)
log("DASS EDA — ML Readiness Report")
log("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – 5-class balance
# REASON: The 5-class problem closely mirrors clinical DASS interpretation but
#         is likely imbalanced.  Plotting this is the first step to deciding
#         whether re-sampling or cost-sensitive learning is needed.
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
fig.suptitle("5-Class Label Distribution (DASS-21 Clinical Severity)", fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    counts = df[f"{subscale}_5cls"].value_counts().reindex(severity_order, fill_value=0)
    bars = ax.bar(severity_order, counts.values, color=severity_colors, edgecolor="white")
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Severity")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=20)
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f"{v:,}\n({100*v/len(df):.1f}%)", ha="center", fontsize=8)
    imbalance_ratio = counts.max() / max(counts.min(), 1)
    log(f"\n  {subscale} 5-class imbalance ratio: {imbalance_ratio:.1f}:1")
    for sev, cnt in counts.items():
        log(f"    {sev:<20}: {cnt:>6,}  ({100*cnt/len(df):.1f}%)")

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "07_class_balance_5class.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 07_class_balance_5class.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Binary label balance
# REASON: Binary screening (Normal vs. Elevated) is often the first clinical
#         decision point and produces a simpler, more robust ML problem.
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Binary Label Distribution (Normal vs. Elevated)", fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    counts = df[f"{subscale}_binary"].value_counts()
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%",
           colors=["#2ecc71","#e74c3c"], startangle=90,
           wedgeprops={"edgecolor":"white","linewidth":2})
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    log(f"\n  {subscale} binary: Normal={counts.get('Normal',0):,}  Elevated={counts.get('Elevated',0):,}")

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "07_class_balance_binary.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 07_class_balance_binary.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – 3-class balance
# REASON: A clinically useful middle ground — Normal / Mild-Moderate / Severe+
#         balances interpretability with granularity for clinical triage.
# ═══════════════════════════════════════════════════════════════════════════════
cls3_order  = ["Normal", "Mild-Moderate", "Severe+"]
cls3_colors = ["#2ecc71", "#f39c12", "#e74c3c"]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("3-Class Label Distribution (Normal / Mild-Moderate / Severe+)", fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    counts = df[f"{subscale}_3cls"].value_counts().reindex(cls3_order, fill_value=0)
    bars = ax.bar(cls3_order, counts.values, color=cls3_colors, edgecolor="white")
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Category"); ax.set_ylabel("Count")
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f"{v:,}\n({100*v/len(df):.1f}%)", ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "07_class_balance_3class.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 07_class_balance_3class.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 – Data quality funnel
# REASON: Shows how many samples remain after applying each quality filter,
#         giving a clear picture of usable training data size.
# ═══════════════════════════════════════════════════════════════════════════════
df["age_num"]   = pd.to_numeric(df["age"], errors="coerce")
df["age_valid"] = df["age_num"].between(13, 100)
vcl_fake_cols   = [v for v in VCL_FAKE if v in df.columns]
df["vcl_fail"]  = df[vcl_fake_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) >= 1
df["testelapse_num"] = pd.to_numeric(df["testelapse"], errors="coerce")
df["too_fast"]  = df["testelapse_num"] < 60

stages = [
    ("Raw Dataset",                len(df)),
    ("Remove Exact Duplicates",    len(df) - df.duplicated().sum()),
    ("Valid Age (13–100)",         df["age_valid"].sum()),
    ("VCL Pass (no fake words)",   (~df["vcl_fail"]).sum()),
    ("Test Time ≥ 60s",            (~df["too_fast"]).sum()),
    ("All Filters Combined",       (~(~df["age_valid"] | df["vcl_fail"] | df["too_fast"])).sum()),
]
log("\n── Data Quality Funnel ─────────────────────────────────────────────────")
for stage, count in stages:
    log(f"  {stage:<30}: {count:,}  ({100*count/len(df):.1f}%)")

labels  = [s[0] for s in stages]
counts  = [s[1] for s in stages]
colors_f= ["#3498db","#2980b9","#1abc9c","#27ae60","#f39c12","#e74c3c"]

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(labels[::-1], counts[::-1], color=colors_f[::-1], edgecolor="white")
ax.set_title("Data Quality Filtering Funnel\n(Samples Remaining After Each Filter)", fontsize=13, weight="bold")
ax.set_xlabel("Number of Respondents")
for bar, v in zip(bars, counts[::-1]):
    ax.text(v + 100, bar.get_y() + bar.get_height()/2,
            f"{v:,}  ({100*v/len(df):.1f}%)", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "07_sample_funnel.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 07_sample_funnel.png")

log("\n── ML Feature Summary ──────────────────────────────────────────────────")
log("  Recommended feature set for ML:")
log("  • 42 DASS-42 item responses (Q1A–Q42A)  — primary predictors")
log("  • 5 Big Five personality composites (TIPI)")
log("  • Demographics: age, gender, education, urban, engnat, familysize")
log("  • Response time features: testelapse, item-level E columns")
log("  • VCL vocabulary sum (real words only) as engagement proxy")
log("\n  Recommended label strategies:")
log("  1. Binary (Normal vs Elevated) — baseline screening model")
log("  2. 3-class (Normal / Mild-Mod / Severe+) — triage model")
log("  3. Regression (continuous score) — fine-grained severity model")

rep_path = os.path.join(OUT_REP, "ml_readiness_report.txt")
with open(rep_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  → Report saved: {rep_path}")
print("[07] DONE\n")
