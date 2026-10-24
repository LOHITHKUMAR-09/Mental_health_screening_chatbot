"""
03_demographics.py
==================
Step 3 – Demographic Analysis & Group Comparisons

PURPOSE & REASON:
  Understanding who took the survey is essential for:
    • Detecting sampling bias (e.g., a sample skewed toward young females
      from one country will not generalise well).
    • Identifying demographic predictors of mental health severity.
    • Informing feature engineering choices for the ML pipeline.

  We analyse: age, gender, education, urban/rural background, country,
  English nativeness, and handedness, and cross-tabulate each with DASS
  severity to find actionable patterns.

OUTPUT:
  outputs/figures/03_age_distribution.png
  outputs/figures/03_gender_breakdown.png
  outputs/figures/03_education_breakdown.png
  outputs/figures/03_country_top20.png
  outputs/figures/03_dass_by_gender.png
  outputs/figures/03_dass_by_age_group.png
  outputs/figures/03_dass_by_education.png
  outputs/reports/demographics_report.txt
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

print("[03] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# ── Compute subscale scores ────────────────────────────────────────────────────
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    return (df[cols].apply(pd.to_numeric, errors="coerce") - 1).sum(axis=1) * 2

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# ── Demographic cleaning ───────────────────────────────────────────────────────
df["age_num"]  = pd.to_numeric(df["age"], errors="coerce")
df["age_valid"]= df["age_num"].between(13, 100)
df["gender_label"]    = df["gender"].astype(str).map(GENDER_MAP)
df["education_label"] = df["education"].astype(str).map(EDUCATION_MAP)
df["urban_label"]     = df["urban"].astype(str).map(URBAN_MAP)
df["engnat_label"]    = df["engnat"].astype(str).map(ENGNAT_MAP)

# Age groups (for groupwise analysis)
# REASON: Continuous age is hard to interpret in bar charts; binning into
#         developmental/life-stage groups reveals age-related patterns.
bins   = [12, 17, 24, 34, 44, 54, 100]
labels = ["13–17", "18–24", "25–34", "35–44", "45–54", "55+"]
df["age_group"] = pd.cut(df.loc[df["age_valid"], "age_num"], bins=bins, labels=labels)

lines = []
def log(m=""):
    print(m); lines.append(m)

log("=" * 60)
log("DASS EDA — Demographics Report")
log("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Age distribution
# REASON: Age is the single most important covariate in mental health research.
#         Heavy skew or narrow range limits generalisability.
# ═══════════════════════════════════════════════════════════════════════════════
age_valid_df = df[df["age_valid"]]["age_num"]
log(f"\nAge (valid 13–100): n={len(age_valid_df):,}, mean={age_valid_df.mean():.1f}, "
    f"median={age_valid_df.median():.1f}, std={age_valid_df.std():.1f}")
log(f"Invalid ages: {(~df['age_valid']).sum():,}")

fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
axes[0].hist(age_valid_df, bins=50, color="#3498db", edgecolor="white")
axes[0].axvline(age_valid_df.mean(),   color="red",  linestyle="--", label=f"Mean {age_valid_df.mean():.1f}")
axes[0].axvline(age_valid_df.median(), color="orange", linestyle=":",  label=f"Median {age_valid_df.median():.1f}")
axes[0].set_title("Age Distribution (valid respondents)", fontsize=12, weight="bold")
axes[0].set_xlabel("Age")
axes[0].set_ylabel("Count")
axes[0].legend()

age_group_counts = df["age_group"].value_counts().sort_index()
axes[1].bar(age_group_counts.index.astype(str), age_group_counts.values, color="#2980b9", edgecolor="white")
axes[1].set_title("Respondents by Age Group", fontsize=12, weight="bold")
axes[1].set_xlabel("Age Group")
axes[1].set_ylabel("Count")
for i, v in enumerate(age_group_counts.values):
    axes[1].text(i, v + 50, f"{v:,}", ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "03_age_distribution.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 03_age_distribution.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Gender & Education breakdown
# ═══════════════════════════════════════════════════════════════════════════════
gender_counts = df["gender_label"].value_counts()
edu_order = ["< High School", "High School", "University", "Graduate", "Unknown"]
edu_counts = df["education_label"].value_counts().reindex(edu_order, fill_value=0)

log(f"\nGender distribution:")
for k, v in gender_counts.items():
    log(f"  {k}: {v:,}  ({100*v/len(df):.1f}%)")
log(f"\nEducation distribution:")
for k, v in edu_counts.items():
    log(f"  {k}: {v:,}  ({100*v/len(df):.1f}%)")

fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
colors_gen = ["#3498db","#e74c3c","#2ecc71","#95a5a6"]
axes[0].pie(gender_counts.values, labels=gender_counts.index,
            autopct="%1.1f%%", colors=colors_gen[:len(gender_counts)],
            startangle=140, wedgeprops={"edgecolor":"white","linewidth":2})
axes[0].set_title("Gender Distribution", fontsize=13, weight="bold")

axes[1].barh(edu_counts.index, edu_counts.values, color="#9b59b6", edgecolor="white")
axes[1].set_title("Education Level Distribution", fontsize=13, weight="bold")
axes[1].set_xlabel("Count")
for i, v in enumerate(edu_counts.values):
    axes[1].text(v + 100, i, f"{v:,}", va="center", fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "03_gender_education.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 03_gender_education.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – Top 20 countries
# REASON: Geographic concentration can introduce cultural bias in self-report
#         mental health data; knowing the distribution helps set expectations
#         for model generalisation.
# ═══════════════════════════════════════════════════════════════════════════════
country_counts = df["country"].value_counts().head(20)
log(f"\nTop 10 countries:")
for c, v in country_counts.head(10).items():
    log(f"  {c}: {v:,}  ({100*v/len(df):.1f}%)")

fig, ax = plt.subplots(figsize=(12, 7))
colors_c = plt.cm.tab20(np.linspace(0, 1, len(country_counts)))
ax.barh(country_counts.index[::-1], country_counts.values[::-1], color=colors_c)
ax.set_title("Top 20 Countries by Respondent Count", fontsize=13, weight="bold")
ax.set_xlabel("Number of Respondents")
for i, v in enumerate(country_counts.values[::-1]):
    ax.text(v + 50, i, f"{v:,}", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "03_country_top20.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 03_country_top20.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 – DASS scores by Gender
# REASON: Literature consistently shows gender differences in depression &
#         anxiety prevalence; verifying this in the data confirms it contains
#         the expected signal and validates the dataset.
# ═══════════════════════════════════════════════════════════════════════════════
gender_filter = df["gender_label"].isin(["Male", "Female"])
gender_plot = df[gender_filter][["gender_label","Depression","Anxiety","Stress"]].melt(
    id_vars="gender_label", var_name="Subscale", value_name="Score")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DASS-21 Scores by Gender (Male vs Female)", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    sub = gender_plot[gender_plot["Subscale"]==subscale]
    sns.boxplot(data=sub, x="gender_label", y="Score",
                palette={"Male":"#3498db","Female":"#e74c3c"}, ax=ax)
    # Mann–Whitney U test
    male_scores   = df[(df["gender_label"]=="Male")]  [subscale].dropna()
    female_scores = df[(df["gender_label"]=="Female")][subscale].dropna()
    u_stat, p_val = stats.mannwhitneyu(male_scores, female_scores, alternative="two-sided")
    sig = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else "ns"))
    ax.set_title(f"{subscale}  (p{sig})", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Gender"); ax.set_ylabel("Score")
    log(f"\n  {subscale} (Mann-Whitney): U={u_stat:.0f}, p={p_val:.4e}, {sig}")

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "03_dass_by_gender.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 03_dass_by_gender.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 – DASS scores by Age Group
# REASON: Younger populations (18–24) show higher mental health burden in
#         general population studies; this analysis checks if the pattern
#         holds here and guides age-stratified modelling.
# ═══════════════════════════════════════════════════════════════════════════════
age_plot = df[df["age_valid"] & df["age_group"].notna()]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DASS-21 Scores by Age Group", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    means = age_plot.groupby("age_group", observed=True)[subscale].mean()
    sems  = age_plot.groupby("age_group", observed=True)[subscale].sem()
    ax.bar(means.index.astype(str), means.values, yerr=sems.values,
           color=PALETTE[subscale], alpha=0.8, edgecolor="white", capsize=4)
    ax.set_title(f"{subscale} by Age Group", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Age Group"); ax.set_ylabel("Mean Score ± SE")
    ax.tick_params(axis="x", rotation=20)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "03_dass_by_age_group.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 03_dass_by_age_group.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 6 – DASS scores by Education Level
# REASON: Education is a known socioeconomic protective factor against mental
#         health disorders. Detecting this gradient strengthens the case for
#         including education as a feature in the ML model.
# ═══════════════════════════════════════════════════════════════════════════════
edu_order_valid = ["< High School", "High School", "University", "Graduate"]
edu_plot = df[df["education_label"].isin(edu_order_valid)]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DASS-21 Mean Scores by Education Level", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    means = edu_plot.groupby("education_label")[subscale].mean().reindex(edu_order_valid)
    sems  = edu_plot.groupby("education_label")[subscale].sem().reindex(edu_order_valid)
    ax.bar(means.index, means.values, yerr=sems.values,
           color=PALETTE[subscale], alpha=0.8, edgecolor="white", capsize=4)
    ax.set_title(f"{subscale}", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Education Level"); ax.set_ylabel("Mean Score ± SE")
    ax.tick_params(axis="x", rotation=15)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "03_dass_by_education.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 03_dass_by_education.png")

rep_path = os.path.join(OUT_REP, "demographics_report.txt")
with open(rep_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  → Report saved: {rep_path}")
print("[03] DONE\n")
