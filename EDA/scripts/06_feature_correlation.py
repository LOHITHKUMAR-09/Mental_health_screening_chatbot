"""
06_feature_correlation.py
=========================
Step 6 – Feature Correlation & Multicollinearity Analysis

PURPOSE & REASON:
  Before feeding features into ML models, we need to understand:
    • Which features (Q items, TIPI, demographics) are most correlated
      with DASS severity — these will be the strongest predictors.
    • Whether any features are so highly correlated with each other
      (multicollinearity) that they add redundant information.
    • The overall feature correlation landscape to inform dimensionality
      reduction (PCA) decisions.

  This script:
    1. Computes a full feature correlation matrix (42 Q items + TIPI + demographics).
    2. Identifies feature clusters (items that measure similar things).
    3. Computes point-biserial / Pearson correlations with the three DASS scores.
    4. Generates a pairplot of DASS scores + top personality predictors.

OUTPUT:
  outputs/figures/06_full_feature_correlation.png
  outputs/figures/06_dass_feature_importance_corr.png
  outputs/figures/06_pairplot_dass_personality.png
  outputs/reports/feature_correlation_report.txt
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
from   scipy import stats

sns.set_theme(style="whitegrid")

print("[06] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# ── DASS scores ───────────────────────────────────────────────────────────────
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    return (df[cols].apply(pd.to_numeric, errors="coerce") - 1).sum(axis=1) * 2

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# ── TIPI scoring ──────────────────────────────────────────────────────────────
tipi_cols = [f"TIPI{i}" for i in range(1, 11)]
df[tipi_cols] = df[tipi_cols].apply(pd.to_numeric, errors="coerce")
df["Extraversion"]      = (df["TIPI1"] + (8 - df["TIPI6"])) / 2
df["Agreeableness"]     = ((8 - df["TIPI2"]) + df["TIPI7"])  / 2
df["Conscientiousness"] = (df["TIPI3"] + (8 - df["TIPI8"]))  / 2
df["Neuroticism"]       = (df["TIPI4"] + (8 - df["TIPI9"]))  / 2
df["Openness"]          = (df["TIPI5"] + (8 - df["TIPI10"])) / 2

big5 = ["Extraversion","Agreeableness","Conscientiousness","Neuroticism","Openness"]

# ── All Q-answer features ─────────────────────────────────────────────────────
q_cols = [f"Q{i}A" for i in range(1, 43)]
df[q_cols] = df[q_cols].apply(pd.to_numeric, errors="coerce")

# ── Numeric demographics ──────────────────────────────────────────────────────
demo_cols = ["age", "gender", "education", "urban", "engnat", "familysize", "screensize"]
df[demo_cols] = df[demo_cols].apply(pd.to_numeric, errors="coerce")

lines = []
def log(m=""):
    print(m); lines.append(m)

log("=" * 60)
log("DASS EDA — Feature Correlation Report")
log("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Q-item inter-correlation heatmap
# REASON: Items within the same subscale should cluster together (high
#         within-subscale correlations confirm construct validity).
#         Cross-subscale correlations reveal shared variance (comorbidity).
# ═══════════════════════════════════════════════════════════════════════════════
q_corr = df[q_cols].corr()

# Reorder by subscale grouping
subscale_order = (
    [f"Q{q}A" for q in sorted(DEPRESSION_QS)] +
    [f"Q{q}A" for q in sorted(ANXIETY_QS)]    +
    [f"Q{q}A" for q in sorted(STRESS_QS)]
)
q_corr_ordered = q_corr.loc[subscale_order, subscale_order]

fig, ax = plt.subplots(figsize=(18, 16))
mask = np.triu(np.ones_like(q_corr_ordered, dtype=bool))
sns.heatmap(q_corr_ordered, ax=ax, cmap="coolwarm", center=0, vmin=-0.2, vmax=1.0,
            linewidths=0.1, mask=mask, cbar_kws={"label": "Pearson r"},
            xticklabels=q_corr_ordered.columns, yticklabels=q_corr_ordered.index)
ax.set_title("DASS Item Inter-Correlation Matrix\n(Grouped by Subscale: Depression | Anxiety | Stress)",
             fontsize=13, weight="bold")
ax.tick_params(axis="both", labelsize=6, rotation=45)

# Add subscale boundary lines
dep_n = len(DEPRESSION_QS)
anx_n = len(ANXIETY_QS)
for pos in [dep_n, dep_n + anx_n]:
    ax.axhline(pos, color="white", lw=2)
    ax.axvline(pos, color="white", lw=2)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "06_full_feature_correlation.png"), dpi=FIG_DPI, bbox_inches="tight")
plt.close()
print("  → Figure saved: 06_full_feature_correlation.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Feature-DASS correlations (bar chart)
# REASON: Shows which individual features are the strongest predictors of each
#         DASS subscale — directly informs which features deserve the most
#         attention during feature engineering.
# ═══════════════════════════════════════════════════════════════════════════════
all_features = q_cols + big5 + ["age", "gender", "education", "urban", "familysize"]
feature_corrs = {}
for subscale in ["Depression", "Anxiety", "Stress"]:
    corrs = {}
    for feat in all_features:
        try:
            valid = df[[feat, subscale]].dropna()
            r, p  = stats.pearsonr(valid[feat], valid[subscale])
            corrs[feat] = r
        except Exception:
            corrs[feat] = np.nan
    feature_corrs[subscale] = corrs

log("\n── Top 10 Positive & Negative Correlates per DASS Subscale ─────────────")
for subscale in ["Depression","Anxiety","Stress"]:
    s = pd.Series(feature_corrs[subscale]).dropna().sort_values()
    log(f"\n  {subscale}:")
    log(f"    Top positive (risk):   {list(s.tail(5).items())}")
    log(f"    Top negative (protect):{list(s.head(5).items())}")

fig, axes = plt.subplots(1, 3, figsize=(22, 8))
fig.suptitle("Feature Correlations with DASS Subscales\n(Top & Bottom 20 features by Pearson r)",
             fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    s = pd.Series(feature_corrs[subscale]).dropna()
    top    = s.nlargest(10)
    bottom = s.nsmallest(10)
    plot_s = pd.concat([bottom, top]).sort_values()
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in plot_s.values]
    ax.barh(plot_s.index, plot_s.values, color=colors, edgecolor="white")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Pearson r")
    ax.tick_params(axis="y", labelsize=7)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "06_dass_feature_importance_corr.png"), dpi=FIG_DPI, bbox_inches="tight")
plt.close()
print("  → Figure saved: 06_dass_feature_importance_corr.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – Pairplot: DASS scores + top personality predictors
# REASON: A pairplot shows both marginal distributions and bivariate
#         relationships simultaneously, revealing non-linear patterns
#         that Pearson r would miss.
# ═══════════════════════════════════════════════════════════════════════════════
pair_cols = ["Depression", "Anxiety", "Stress", "Neuroticism", "Conscientiousness", "Extraversion"]
pair_df = df[pair_cols].dropna().sample(min(5000, len(df)), random_state=42)

g = sns.pairplot(pair_df, diag_kind="kde", plot_kws={"alpha": 0.15, "s": 5},
                 diag_kws={"fill": True})
g.fig.suptitle("Pairplot: DASS Subscales + Key Personality Traits\n(Sampled 5,000 respondents)",
               fontsize=13, weight="bold", y=1.01)

g.savefig(os.path.join(OUT_FIG, "06_pairplot_dass_personality.png"), dpi=120, bbox_inches="tight")
plt.close()
print("  → Figure saved: 06_pairplot_dass_personality.png")

rep_path = os.path.join(OUT_REP, "feature_correlation_report.txt")
with open(rep_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  → Report saved: {rep_path}")
print("[06] DONE\n")
