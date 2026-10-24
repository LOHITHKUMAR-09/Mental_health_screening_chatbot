"""
02_dass_scores.py
=================
Step 2 – DASS Subscale Score Computation & Distribution Analysis

PURPOSE & REASON:
  The raw data contains 42 individual question responses. To make clinical
  sense of them, we must:
    • Compute validated Depression, Anxiety, and Stress subscale scores
      following Lovibond & Lovibond (1995) scoring rules.
    • Multiply by 2 to convert from DASS-42 scale to DASS-21 equivalent
      (standard in research so results are comparable across studies).
    • Classify each respondent into severity bands (Normal → Extremely Severe).
    • Visualise the full score distributions, severity breakdowns, and
      co-morbidity patterns (how often do D, A, S co-occur?).

OUTPUT:
  outputs/figures/02_score_distributions.png
  outputs/figures/02_severity_breakdown.png
  outputs/figures/02_comorbidity_heatmap.png
  outputs/figures/02_score_boxplots.png
  outputs/figures/02_score_correlations.png
  outputs/reports/dass_score_summary.txt
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config_loader import *   # noqa

import pandas as pd
import numpy  as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from   scipy   import stats

sns.set_theme(style="whitegrid")

print("[02] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# ── Score computation ─────────────────────────────────────────────────────────
# REASON: Responses are on a 1–4 scale; DASS scoring requires 0–3.
#         Each subscale sums 14 items × (0–3) = 0–42 raw, × 2 → 0–84 DASS-21.
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    numeric = df[cols].apply(pd.to_numeric, errors="coerce")
    return (numeric - 1).sum(axis=1) * 2   # shift to 0-3, sum, ×2

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# ── Severity classification ────────────────────────────────────────────────────
def classify_severity(score, bands):
    for lo, hi, label in bands:
        if lo <= score <= hi:
            return label
    return "Unknown"

for subscale, bands in SEVERITY.items():
    df[f"{subscale}_Severity"] = df[subscale].apply(classify_severity, bands=bands)

severity_order = ["Normal", "Mild", "Moderate", "Severe", "Extremely Severe"]
severity_colors = [PALETTE[s] for s in severity_order]

# ── Report ─────────────────────────────────────────────────────────────────────
lines = []
def log(m=""):
    print(m); lines.append(m)

log("=" * 60)
log("DASS-21 Score Summary Report")
log("=" * 60)

for subscale in ["Depression", "Anxiety", "Stress"]:
    s = df[subscale]
    log(f"\n── {subscale} ──────────────────────────────────────────────")
    log(f"  n       : {s.notna().sum():,}")
    log(f"  Mean    : {s.mean():.2f}")
    log(f"  Median  : {s.median():.2f}")
    log(f"  Std dev : {s.std():.2f}")
    log(f"  Min–Max : {s.min():.0f} – {s.max():.0f}")
    log(f"  Skewness: {s.skew():.3f}")
    log(f"  Kurtosis: {s.kurt():.3f}")
    log(f"\n  Severity breakdown:")
    for sev in severity_order:
        count = (df[f"{subscale}_Severity"] == sev).sum()
        log(f"    {sev:<20}: {count:>6,}  ({100*count/len(df):.1f}%)")

# Correlation
log("\n── Subscale Pearson Correlations ───────────────────────────────────────")
for a, b in [("Depression","Anxiety"),("Depression","Stress"),("Anxiety","Stress")]:
    r, p = stats.pearsonr(df[a].dropna(), df[b].dropna())
    log(f"  {a} vs {b}: r = {r:.3f}  (p {'< 0.001' if p < 0.001 else f'= {p:.4f}'})")

rep_path = os.path.join(OUT_REP, "dass_score_summary.txt")
with open(rep_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  → Report saved: {rep_path}")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Score distributions (histogram + KDE)
# REASON: Shows whether scores are normally distributed or skewed; critical
#         for choosing appropriate ML models and preprocessing strategies.
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("DASS-21 Score Distributions (n = {:,})".format(len(df)), fontsize=15, weight="bold")

for ax, subscale in zip(axes, ["Depression", "Anxiety", "Stress"]):
    color = PALETTE[subscale]
    data = df[subscale].dropna()
    ax.hist(data, bins=60, density=True, alpha=0.55, color=color, edgecolor="white")
    kde_x = np.linspace(0, data.max(), 300)
    kde   = stats.gaussian_kde(data)
    ax.plot(kde_x, kde(kde_x), color=color, lw=2.5)
    ax.axvline(data.mean(),   color="black",  linestyle="--", lw=1.5, label=f"Mean {data.mean():.1f}")
    ax.axvline(data.median(), color="gray",   linestyle=":",  lw=1.5, label=f"Median {data.median():.1f}")
    ax.set_title(subscale, fontsize=13, weight="bold", color=color)
    ax.set_xlabel("DASS-21 Score")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "02_score_distributions.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 02_score_distributions.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Severity breakdown (stacked bar)
# REASON: Translates continuous scores into clinically meaningful categories.
#         Shows the proportion of the sample at each severity level, which is
#         the primary label distribution for the ML classification task.
# ═══════════════════════════════════════════════════════════════════════════════
sev_data = {}
for subscale in ["Depression", "Anxiety", "Stress"]:
    counts = df[f"{subscale}_Severity"].value_counts()
    sev_data[subscale] = [counts.get(s, 0) / len(df) * 100 for s in severity_order]

sev_df = pd.DataFrame(sev_data, index=severity_order)

fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Grouped bar
sev_df.T.plot(kind="bar", ax=axes[0], color=severity_colors, width=0.7, edgecolor="white")
axes[0].set_title("Severity Level Distribution per Subscale", fontsize=13, weight="bold")
axes[0].set_ylabel("% of Respondents")
axes[0].set_xlabel("Subscale")
axes[0].set_xticklabels(["Depression", "Anxiety", "Stress"], rotation=0)
axes[0].legend(title="Severity", bbox_to_anchor=(1.01, 1), loc="upper left")

# Stacked bar
sev_df.T.plot(kind="bar", stacked=True, ax=axes[1], color=severity_colors, width=0.6, edgecolor="white")
axes[1].set_title("Cumulative Severity Proportions", fontsize=13, weight="bold")
axes[1].set_ylabel("% of Respondents")
axes[1].set_xlabel("Subscale")
axes[1].set_xticklabels(["Depression", "Anxiety", "Stress"], rotation=0)
axes[1].legend(title="Severity", bbox_to_anchor=(1.01, 1), loc="upper left")

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "02_severity_breakdown.png"), dpi=FIG_DPI, bbox_inches="tight")
plt.close()
print("  → Figure saved: 02_severity_breakdown.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – Co-morbidity heatmap
# REASON: Depression, Anxiety and Stress frequently co-occur. Understanding
#         their joint severity is important for multi-label classification.
# ═══════════════════════════════════════════════════════════════════════════════
# Use binary flag: "Elevated" = Moderate, Severe, or Extremely Severe
for subscale in ["Depression", "Anxiety", "Stress"]:
    df[f"{subscale}_Elevated"] = df[f"{subscale}_Severity"].isin(
        ["Moderate", "Severe", "Extremely Severe"]).astype(int)

comorbidity = pd.DataFrame({
    "D+A": ((df["Depression_Elevated"]==1) & (df["Anxiety_Elevated"]==1)).sum(),
    "D+S": ((df["Depression_Elevated"]==1) & (df["Stress_Elevated"]==1)).sum(),
    "A+S": ((df["Anxiety_Elevated"]==1)    & (df["Stress_Elevated"]==1)).sum(),
    "D+A+S": ((df["Depression_Elevated"]==1) & (df["Anxiety_Elevated"]==1) &
               (df["Stress_Elevated"]==1)).sum(),
    "D only": ((df["Depression_Elevated"]==1) & (df["Anxiety_Elevated"]==0) &
                (df["Stress_Elevated"]==0)).sum(),
    "A only": ((df["Anxiety_Elevated"]==1)    & (df["Depression_Elevated"]==0) &
                (df["Stress_Elevated"]==0)).sum(),
    "S only": ((df["Stress_Elevated"]==1)     & (df["Depression_Elevated"]==0) &
                (df["Anxiety_Elevated"]==0)).sum(),
    "None":   ((df["Depression_Elevated"]==0) & (df["Anxiety_Elevated"]==0) &
                (df["Stress_Elevated"]==0)).sum(),
}, index=["Count"]).T

# Subscale pairwise correlation heatmap
corr_mat = df[["Depression", "Anxiety", "Stress"]].corr()

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(corr_mat, annot=True, fmt=".3f", cmap="coolwarm", center=0,
            linewidths=0.5, ax=axes[0], annot_kws={"size": 14})
axes[0].set_title("Pearson Correlation Between Subscales", fontsize=13, weight="bold")

comorbidity_pct = 100 * comorbidity / len(df)
colors_combo = ["#3498db","#e74c3c","#f39c12","#8e44ad","#1abc9c","#27ae60","#d35400","#95a5a6"]
axes[1].barh(comorbidity_pct.index, comorbidity_pct["Count"], color=colors_combo)
axes[1].set_title("Elevated Symptom Co-occurrence Patterns\n(Moderate+ on each subscale)", fontsize=13, weight="bold")
axes[1].set_xlabel("% of All Respondents")
for i, v in enumerate(comorbidity_pct["Count"]):
    axes[1].text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "02_comorbidity_heatmap.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 02_comorbidity_heatmap.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 – Boxplots per severity
# REASON: Boxplots reveal within-group spread; verifies severity thresholds
#         genuinely separate score ranges as expected.
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Score Distribution Within Each Severity Category", fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression", "Anxiety", "Stress"]):
    sev_col = f"{subscale}_Severity"
    plot_df = df[[subscale, sev_col]].dropna()
    plot_df[sev_col] = pd.Categorical(plot_df[sev_col], categories=severity_order, ordered=True)
    plot_df = plot_df.sort_values(sev_col)
    sns.boxplot(data=plot_df, x=sev_col, y=subscale,
                palette=dict(zip(severity_order, severity_colors)), ax=ax)
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Severity")
    ax.set_ylabel("Score")
    ax.tick_params(axis="x", rotation=20)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "02_score_boxplots.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 02_score_boxplots.png")

print("[02] DONE\n")
