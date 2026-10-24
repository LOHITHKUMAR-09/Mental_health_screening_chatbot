"""
05_personality_vcl.py
=====================
Step 5 – Big Five Personality (TIPI) & Vocabulary Check (VCL) Analysis

PURPOSE & REASON:
  The survey collected two supplementary instruments:
    • TIPI (Ten-Item Personality Inventory): measures the Big Five traits
      (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism).
      These traits are known correlates of mental health; including them may
      boost ML model performance.
    • VCL (Vocabulary Check List): 16 words (13 real, 3 fake) to detect
      careless respondents.  High rates of endorsing fake words = unreliable data.

  This script:
    1. Computes Big Five composite scores from TIPI (standard reverse-scoring).
    2. Correlates Big Five traits with DASS subscales.
    3. Analyses VCL patterns and validity filter impact.
    4. Tests whether excluding VCL-failed respondents changes DASS score distributions.

OUTPUT:
  outputs/figures/05_tipi_distributions.png
  outputs/figures/05_tipi_dass_correlations.png
  outputs/figures/05_vcl_filter_impact.png
  outputs/reports/personality_vcl_report.txt
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

print("[05] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# ── DASS scores ───────────────────────────────────────────────────────────────
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    return (df[cols].apply(pd.to_numeric, errors="coerce") - 1).sum(axis=1) * 2

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# ── TIPI Big Five scoring ─────────────────────────────────────────────────────
# REASON: The TIPI uses a 1–7 scale. Some items are reverse-scored (R) per
# Gosling et al. (2003): TIPI2R, TIPI4R, TIPI6R, TIPI8R, TIPI10R.
# Big Five composite = (forward item + (8 - reverse item)) / 2
tipi_cols = [f"TIPI{i}" for i in range(1, 11)]
df[tipi_cols] = df[tipi_cols].apply(pd.to_numeric, errors="coerce")

df["Extraversion"]      = (df["TIPI1"] + (8 - df["TIPI6"])) / 2
df["Agreeableness"]     = ((8 - df["TIPI2"]) + df["TIPI7"])  / 2
df["Conscientiousness"] = (df["TIPI3"] + (8 - df["TIPI8"]))  / 2
df["Neuroticism"]       = (df["TIPI4"] + (8 - df["TIPI9"]))  / 2
df["Openness"]          = (df["TIPI5"] + (8 - df["TIPI10"])) / 2

big5 = ["Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]
big5_colors = ["#3498db", "#2ecc71", "#9b59b6", "#e74c3c", "#f39c12"]

lines = []
def log(m=""):
    print(m); lines.append(m)

log("=" * 60)
log("DASS EDA — Personality & VCL Report")
log("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Big Five trait distributions
# REASON: Confirms the TIPI items were answered thoughtfully (reasonable spread
#         with no extreme ceiling/floor effects) and shows trait prevalence.
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Big Five Personality Trait Distributions (TIPI, 1–7 scale)", fontsize=14, weight="bold")
axes_flat = axes.flatten()

for ax, trait, color in zip(axes_flat, big5, big5_colors):
    data = df[trait].dropna()
    ax.hist(data, bins=30, color=color, alpha=0.7, edgecolor="white")
    ax.axvline(data.mean(), color="black", linestyle="--", lw=2, label=f"Mean {data.mean():.2f}")
    ax.set_title(trait, fontsize=12, weight="bold", color=color)
    ax.set_xlabel("Score (1–7)")
    ax.set_ylabel("Count")
    ax.legend(fontsize=9)
    log(f"\n  {trait}: mean={data.mean():.2f}, median={data.median():.2f}, std={data.std():.2f}")

axes_flat[-1].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "05_tipi_distributions.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 05_tipi_distributions.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Big Five ↔ DASS correlation heatmap
# REASON: This reveals which personality traits are risk/protective factors.
#         High Neuroticism is well-established as a transdiagnostic risk factor;
#         high Conscientiousness and Extraversion are protective.
#         Confirming these patterns validates the dataset and identifies strong
#         ML features.
# ═══════════════════════════════════════════════════════════════════════════════
combo = df[big5 + ["Depression", "Anxiety", "Stress"]].dropna()
corr  = combo.corr()

# Sub-matrix: Big5 rows × DASS columns
corr_sub = corr.loc[big5, ["Depression", "Anxiety", "Stress"]]

log("\n── Big Five ↔ DASS Pearson Correlations ─────────────────────────────────")
for trait in big5:
    for subscale in ["Depression","Anxiety","Stress"]:
        r, p = stats.pearsonr(df[trait].dropna(), df[subscale][df[trait].notna()])
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
        log(f"  {trait:<20} × {subscale:<12}: r = {r:+.3f}  {sig}")

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

sns.heatmap(corr_sub, annot=True, fmt=".3f", cmap="coolwarm", center=0,
            linewidths=0.5, ax=axes[0], annot_kws={"size": 12},
            cbar_kws={"label": "Pearson r"})
axes[0].set_title("Big Five Personality × DASS Subscale Correlations\n(Negative = protective, Positive = risk factor)",
                  fontsize=12, weight="bold")

# Full Big5 + DASS correlation matrix
mask = np.zeros_like(corr, dtype=bool)
mask[np.triu_indices_from(mask)] = True
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
            linewidths=0.3, ax=axes[1], mask=mask, annot_kws={"size": 7},
            cbar_kws={"label": "Pearson r"})
axes[1].set_title("Full Correlation Matrix:\nBig Five + DASS Subscales", fontsize=12, weight="bold")
axes[1].tick_params(axis="x", rotation=45, labelsize=8)
axes[1].tick_params(axis="y", rotation=0,  labelsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "05_tipi_dass_correlations.png"), dpi=FIG_DPI, bbox_inches="tight")
plt.close()
print("  → Figure saved: 05_tipi_dass_correlations.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – VCL Validity filter impact
# REASON: Respondents endorsing fake words may provide unreliable DASS
#         responses.  We test whether excluding them significantly changes the
#         score distributions — if it does, validity filtering is warranted
#         before model training.
# ═══════════════════════════════════════════════════════════════════════════════
vcl_fake_cols = [v for v in VCL_FAKE if v in df.columns]
df["vcl_fail"] = df[vcl_fake_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) >= 1

n_fail  = df["vcl_fail"].sum()
n_pass  = (~df["vcl_fail"]).sum()
log(f"\n── VCL Validity Filter ──────────────────────────────────────────────────")
log(f"  VCL PASS: {n_pass:,}  ({100*n_pass/len(df):.1f}%)")
log(f"  VCL FAIL: {n_fail:,}  ({100*n_fail/len(df):.1f}%)")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DASS Scores: VCL Valid vs. Invalid Respondents\n(Invalid = endorsed ≥1 fake vocabulary word)",
             fontsize=13, weight="bold")

for ax, subscale in zip(axes, ["Depression", "Anxiety", "Stress"]):
    pass_scores = df[~df["vcl_fail"]][subscale].dropna()
    fail_scores = df[df["vcl_fail"]][subscale].dropna()

    ax.hist(pass_scores, bins=50, alpha=0.6, color="#2ecc71", label=f"Valid (n={len(pass_scores):,})", density=True)
    ax.hist(fail_scores, bins=50, alpha=0.6, color="#e74c3c", label=f"Invalid (n={len(fail_scores):,})", density=True)

    u, p = stats.mannwhitneyu(pass_scores, fail_scores, alternative="two-sided")
    sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
    log(f"\n  {subscale} VCL pass vs fail: U={u:.0f}, p={p:.4e} {sig}")
    log(f"    Pass mean={pass_scores.mean():.1f}  |  Fail mean={fail_scores.mean():.1f}")

    ax.set_title(f"{subscale}  (p{sig})", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Score")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "05_vcl_filter_impact.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 05_vcl_filter_impact.png")

rep_path = os.path.join(OUT_REP, "personality_vcl_report.txt")
with open(rep_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  → Report saved: {rep_path}")
print("[05] DONE\n")
