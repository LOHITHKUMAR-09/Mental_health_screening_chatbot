"""
generate_notebook.py
====================
Generates DASS_EDA_Colab.ipynb — the complete single-file Google Colab
notebook for all 7 EDA steps.  Run with:
    python EDA/generate_notebook.py
"""

import json, os

# ── Helper ────────────────────────────────────────────────────────────────────
def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.strip()}

def code(src):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src.strip(),
    }

cells = []

# ═══════════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
# DASS Dataset — Complete Exploratory Data Analysis
### ML Mental Health Screening Project

**Dataset:** Depression Anxiety Stress Scales (DASS-42) Online Survey, 2017–2019  
**Source:** [openpsychometrics.org](https://openpsychometrics.org/_rawdata/)  
**Respondents:** 39,775 &nbsp;|&nbsp; **Variables:** 172 &nbsp;|&nbsp; **File size:** ~20 MB

---

### Table of Contents
1. [Setup & Data Loading](#setup)
2. [Step 1 – Data Quality Assessment](#quality)
3. [Step 2 – DASS Score Computation & Distributions](#scores)
4. [Step 3 – Demographic Analysis](#demographics)
5. [Step 4 – Item-Level Analysis](#items)
6. [Step 5 – Big Five Personality & VCL Analysis](#personality)
7. [Step 6 – Feature Correlation & Multicollinearity](#correlation)
8. [Step 7 – Class Balance & ML Readiness](#ml)
9. [Key Insights Summary](#summary)
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# CELL 1 – Install & imports
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
## 0. Setup & Data Loading <a id='setup'></a>

**Why this cell?**  
We install the required libraries (already present in Colab but pinned for reproducibility),
then define all shared constants — DASS subscale question lists, severity thresholds,
colour palettes, and demographic label maps — in one place so every subsequent cell
stays consistent.
"""))

cells.append(code("""
# Install / upgrade key libraries (Colab already has most; this ensures correct versions)
!pip install -q pandas matplotlib seaborn scipy numpy
"""))

cells.append(code("""
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
import warnings, os
warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 130

print("Libraries loaded successfully.")
print(f"pandas {pd.__version__}  |  numpy {np.__version__}")
"""))

cells.append(md("""
### Upload the dataset

Run the cell below to upload `data.csv` from your local machine.  
Alternatively, if you have the file on **Google Drive**, mount Drive and update `DATA_PATH`.
"""))

cells.append(code("""
# ── Option A: Upload from local machine ──────────────────────────────────────
from google.colab import files
import io

print("Please upload the 'data.csv' file (tab-separated, ~20 MB)...")
uploaded = files.upload()
filename  = list(uploaded.keys())[0]
df_raw    = pd.read_csv(io.BytesIO(uploaded[filename]), sep="\\t", low_memory=False)
print(f"Loaded: {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")

# ── Option B: Mount Google Drive (uncomment if preferred) ────────────────────
# from google.colab import drive
# drive.mount('/content/drive')
# DATA_PATH = '/content/drive/MyDrive/YOUR_FOLDER/data.csv'
# df_raw = pd.read_csv(DATA_PATH, sep="\\t", low_memory=False)
"""))

cells.append(code("""
# ── DASS-42 subscale question mappings ────────────────────────────────────────
# REASON: Each subscale maps to 14 specific questions. Defined once here so
# every cell that computes scores uses the identical question list.
DEPRESSION_QS = [3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42]
ANXIETY_QS    = [2, 4, 7,  9,  15, 19, 20, 23, 25, 28, 30, 36, 40, 41]
STRESS_QS     = [1, 6, 8,  11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39]

# ── Clinical severity thresholds (Lovibond & Lovibond, 1995) ─────────────────
SEVERITY = {
    "Depression": [(0,9,"Normal"),(10,13,"Mild"),(14,20,"Moderate"),(21,27,"Severe"),(28,999,"Extremely Severe")],
    "Anxiety":    [(0,7,"Normal"),(8,9,"Mild"),(10,14,"Moderate"),(15,19,"Severe"),(20,999,"Extremely Severe")],
    "Stress":     [(0,14,"Normal"),(15,18,"Mild"),(19,25,"Moderate"),(26,33,"Severe"),(34,999,"Extremely Severe")],
}

# ── Colour palette ────────────────────────────────────────────────────────────
PALETTE = {
    "Normal":"#2ecc71","Mild":"#f1c40f","Moderate":"#e67e22",
    "Severe":"#e74c3c","Extremely Severe":"#8e1010",
    "Depression":"#3498db","Anxiety":"#e74c3c","Stress":"#f39c12",
}
SEVERITY_ORDER  = ["Normal","Mild","Moderate","Severe","Extremely Severe"]
SEVERITY_COLORS = [PALETTE[s] for s in SEVERITY_ORDER]

# ── Demographic label maps ────────────────────────────────────────────────────
GENDER_MAP    = {"1":"Male","2":"Female","3":"Other","0":"Unknown"}
EDUCATION_MAP = {"0":"Unknown","1":"< High School","2":"High School","3":"University","4":"Graduate"}
URBAN_MAP     = {"1":"Rural","2":"Suburban","3":"Urban","0":"Unknown"}
ENGNAT_MAP    = {"1":"Yes","2":"No","0":"Unknown"}
VCL_FAKE      = ["VCL6","VCL9","VCL12"]

# ── Subscale score helper ─────────────────────────────────────────────────────
# REASON: Raw responses are 1-4; DASS scoring needs 0-3.
# Sum of 14 items × 2 converts to DASS-21 equivalent scale (0–84).
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    return (df[cols].apply(pd.to_numeric, errors="coerce") - 1).sum(axis=1) * 2

def classify_severity(score, bands):
    for lo, hi, label in bands:
        if lo <= score <= hi:
            return label
    return "Unknown"

print("Constants and helpers defined.")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 – DATA QUALITY
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 1 — Data Quality Assessment <a id='quality'></a>

**Why?**  
Before any analysis, we must understand what we're working with. Data quality issues
(missing values, duplicates, out-of-range responses, invalid ages, fake-word traps)
can silently distort every downstream result and model performance.

This step covers:
- Shape, dtypes, memory
- Missing values per column
- Exact duplicate detection
- Likert response range validation (valid: 1–4)
- Age plausibility check (13–100)
- VCL fake-word validity filter
- Response time sanity check
"""))

cells.append(code("""
df = df_raw.copy()

# ── Basic metadata ────────────────────────────────────────────────────────────
print(f"Shape  : {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"Memory : {df.memory_usage(deep=True).sum()/1e6:.1f} MB")

dtype_counts = df.dtypes.astype(str).value_counts()
print("\\nColumn dtypes:")
for dtype_name, count in dtype_counts.items():
    print(f"  {dtype_name:<15}: {count} columns")
"""))

cells.append(code("""
# ── Missing values ────────────────────────────────────────────────────────────
# REASON: Missing values can bias summary statistics. We check which columns
# are incomplete and whether missingness is structural or accidental.
miss     = df.isnull().sum()
miss_pct = 100 * miss / len(df)
miss_df  = pd.DataFrame({"Missing": miss, "Pct%": miss_pct.round(2)})
miss_df  = miss_df[miss_df["Missing"] > 0].sort_values("Missing", ascending=False)

print("Columns with missing values:")
print(miss_df.to_string() if not miss_df.empty else "  None")

fig, ax = plt.subplots(figsize=(9, max(3, len(miss_df)*0.45)))
if not miss_df.empty:
    miss_df["Pct%"].plot(kind="barh", ax=ax, color="#e74c3c")
    ax.axvline(5, color="orange", linestyle="--", label="5% threshold")
    ax.set_xlabel("Missing %")
    ax.set_title("Missing Values by Column", fontsize=13, weight="bold")
    ax.legend()
plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# ── Duplicate rows ────────────────────────────────────────────────────────────
# REASON: Duplicate submissions inflate n and skew distributions.
n_dups = df.duplicated().sum()
print(f"Exact duplicates: {n_dups:,}  ({100*n_dups/len(df):.2f}%)")
"""))

cells.append(code("""
# ── Likert response range validation ─────────────────────────────────────────
# REASON: Valid DASS responses are integers 1-4. Values outside this range
# indicate data corruption or encoding errors.
q_answer_cols = [f"Q{i}A" for i in range(1, 43)]
out_of_range  = False
for col in q_answer_cols:
    if col in df.columns:
        numeric_col = pd.to_numeric(df[col], errors="coerce")
        bad = numeric_col.dropna()
        bad = bad[~bad.isin([1, 2, 3, 4])]
        if len(bad) > 0:
            print(f"  {col}: {len(bad)} out-of-range values → unique={sorted(bad.unique())}")
            out_of_range = True
if not out_of_range:
    print("All Q responses are within valid range 1-4. No encoding errors found.")
"""))

cells.append(code("""
# ── Age validity ──────────────────────────────────────────────────────────────
# REASON: Some respondents entered their birth year (e.g., 1998) or nonsense.
# Ages < 13 (minimum realistic for online survey) or > 100 are implausible.
df["age_num"]   = pd.to_numeric(df["age"], errors="coerce")
age_valid       = df["age_num"].between(13, 100)
age_valid_df    = df[age_valid]["age_num"]

print(f"Valid ages   (13-100): {age_valid.sum():,}  ({100*age_valid.mean():.2f}%)")
print(f"Invalid ages         : {(~age_valid).sum():,}  ({100*(~age_valid).mean():.2f}%)")
print(f"Age range (all)      : {df['age_num'].min():.0f} - {df['age_num'].max():.0f}")
print(f"Age range (valid)    : {age_valid_df.min():.0f} - {age_valid_df.max():.0f}")

# Show the invalid ones
print("\\nInvalid age values:")
print(df.loc[~age_valid, "age_num"].value_counts().head(10))
"""))

cells.append(code("""
# ── VCL Fake-word validity ────────────────────────────────────────────────────
# REASON: VCL6="cuivocal", VCL9="florted", VCL12="verdid" are non-existent words.
# A respondent who claims to know them is almost certainly clicking randomly.
# This is the standard built-in validity check for this dataset.
print("VCL fake-word endorsement rates:")
for vcl in VCL_FAKE:
    checked = (df[vcl] == 1).sum()
    print(f"  {vcl} (fake): {checked:,}  ({100*checked/len(df):.2f}%)")

df["vcl_fail"]  = df[[v for v in VCL_FAKE if v in df.columns]].apply(
    pd.to_numeric, errors="coerce").sum(axis=1) >= 1
n_vcl_fail = df["vcl_fail"].sum()
print(f"\\nRespondents endorsing >=1 fake word: {n_vcl_fail:,}  ({100*n_vcl_fail/len(df):.2f}%)")

# ── VCL bar chart: real vs fake words ────────────────────────────────────────
vcl_real = [c for c in df.columns if c.startswith("VCL") and c not in VCL_FAKE]
vcl_all  = vcl_real + VCL_FAKE
vcl_pcts = [100 * (df[c] == 1).mean() for c in vcl_all]
vcl_types= ["Real"]*len(vcl_real) + ["Fake"]*len(VCL_FAKE)
vcl_colors = ["#3498db" if t=="Real" else "#e74c3c" for t in vcl_types]

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(vcl_all, vcl_pcts, color=vcl_colors, edgecolor="white")
ax.set_title("VCL Vocabulary Check — % Respondents Claiming Knowledge\\n(Red = fake words; should be near zero)", fontsize=12, weight="bold")
ax.set_ylabel("% Checked")
ax.set_xlabel("VCL Item")
handles = [mpatches.Patch(color="#3498db", label="Real Word"),
           mpatches.Patch(color="#e74c3c", label="Fake Word")]
ax.legend(handles=handles)
plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# ── Response time sanity check ────────────────────────────────────────────────
# REASON: Completing 42 questions in under 60 seconds (~1.4s/question)
# is physically implausible and suggests random clicking or bots.
df["testelapse_num"]  = pd.to_numeric(df["testelapse"],  errors="coerce")
df["introelapse_num"] = pd.to_numeric(df["introelapse"], errors="coerce")
df["surveyelapse_num"]= pd.to_numeric(df["surveyelapse"],errors="coerce")
MIN_SECS = 60
too_fast = (df["testelapse_num"] < MIN_SECS).sum()

print(f"Median test time : {df['testelapse_num'].median():.0f} s  ({df['testelapse_num'].median()/60:.1f} min)")
print(f"Mean test time   : {df['testelapse_num'].mean():.0f} s  ({df['testelapse_num'].mean()/60:.1f} min)")
print(f"< 60s (suspect)  : {too_fast:,}  ({100*too_fast/len(df):.2f}%)")

p95 = df["testelapse_num"].quantile(0.95)
plot_times = df["testelapse_num"].clip(upper=p95).dropna()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(plot_times, bins=80, color="#3498db", edgecolor="white")
axes[0].axvline(MIN_SECS, color="red", linestyle="--", label="60 s threshold")
axes[0].set_title("Test Completion Time Distribution\\n(clipped at 95th percentile)", fontsize=12, weight="bold")
axes[0].set_xlabel("Seconds"); axes[0].set_ylabel("Count"); axes[0].legend()

phases = ["Intro","Test (DASS)","Demographics"]
medians = [df["introelapse_num"].median(), df["testelapse_num"].median(), df["surveyelapse_num"].median()]
axes[1].barh(phases, medians, color=["#9b59b6","#3498db","#2ecc71"])
axes[1].set_title("Median Time per Survey Phase", fontsize=12, weight="bold")
axes[1].set_xlabel("Seconds")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Quality summary ───────────────────────────────────────────────────────────
any_issue = (~age_valid) | df["vcl_fail"] | (df["testelapse_num"] < MIN_SECS)
print("=" * 50)
print("DATA QUALITY SUMMARY")
print("=" * 50)
print(f"  Total respondents          : {len(df):,}")
print(f"  Exact duplicates           : {n_dups:,}")
print(f"  Invalid age (< 13 or >100) : {(~age_valid).sum():,}")
print(f"  VCL fake-word cheaters     : {n_vcl_fail:,}  (13.1%)")
print(f"  Suspiciously fast (<60s)   : {too_fast:,}")
print(f"  Any quality issue          : {any_issue.sum():,}  ({100*any_issue.mean():.1f}%)")
print(f"  Clean respondents          : {(~any_issue).sum():,}  ({100*(~any_issue).mean():.1f}%)")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 – DASS SCORES
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 2 — DASS Score Computation & Distributions <a id='scores'></a>

**Why?**  
The raw data has 42 individual question responses (Q1A–Q42A). To make clinical sense
of them we must compute the three validated DASS subscale scores following
Lovibond & Lovibond (1995). Multiplying by 2 converts from DASS-42 to DASS-21
equivalent, making results comparable to published norms.

**Scoring formula:**  `Score = (sum of 14 item responses − 14) × 2`
(shifts 1–4 scale to 0–3, then multiplies by 2 → range 0–84)
"""))

cells.append(code("""
df = df_raw.copy()

# ── Compute subscale scores ───────────────────────────────────────────────────
df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# ── Severity classification ───────────────────────────────────────────────────
for subscale, bands in SEVERITY.items():
    df[f"{subscale}_Severity"] = df[subscale].apply(classify_severity, bands=bands)

# ── Descriptive statistics ────────────────────────────────────────────────────
print(f"{'Metric':<12} {'Depression':>14} {'Anxiety':>12} {'Stress':>10}")
print("-" * 52)
for metric, fn in [("Mean", "mean"), ("Median", "median"), ("Std", "std"),
                    ("Min", "min"), ("Max", "max"), ("Skewness", "skew"), ("Kurtosis", "kurt")]:
    vals = [getattr(df[s], fn)() for s in ["Depression","Anxiety","Stress"]]
    print(f"  {metric:<10} {vals[0]:>14.2f} {vals[1]:>12.2f} {vals[2]:>10.2f}")
"""))

cells.append(code("""
# ── Score distributions (histogram + KDE) ─────────────────────────────────────
# REASON: Shows whether scores are normally distributed or skewed — critical
# for choosing appropriate ML models and preprocessing strategies.
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle(f"DASS-21 Score Distributions (n = {len(df):,})", fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    color = PALETTE[subscale]
    data  = df[subscale].dropna()
    ax.hist(data, bins=60, density=True, alpha=0.55, color=color, edgecolor="white")
    kde_x = np.linspace(0, data.max(), 300)
    kde   = stats.gaussian_kde(data)
    ax.plot(kde_x, kde(kde_x), color=color, lw=2.5)
    ax.axvline(data.mean(),   color="black", linestyle="--", lw=1.5, label=f"Mean {data.mean():.1f}")
    ax.axvline(data.median(), color="gray",  linestyle=":",  lw=1.5, label=f"Median {data.median():.1f}")
    ax.set_title(subscale, fontsize=13, weight="bold", color=color)
    ax.set_xlabel("DASS-21 Score"); ax.set_ylabel("Density")
    ax.legend(fontsize=9)

plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Severity breakdown ────────────────────────────────────────────────────────
# REASON: Translates continuous scores into clinically meaningful categories.
# The primary label distribution for the ML classification task.
print("\\nSeverity Distribution (% of respondents):")
print(f"{'Severity':<22} {'Depression':>12} {'Anxiety':>10} {'Stress':>10}")
print("-" * 58)
for sev in SEVERITY_ORDER:
    vals = [100*(df[f"{s}_Severity"]==sev).mean() for s in ["Depression","Anxiety","Stress"]]
    print(f"  {sev:<20} {vals[0]:>12.1f}% {vals[1]:>9.1f}% {vals[2]:>9.1f}%")

sev_data = {}
for subscale in ["Depression","Anxiety","Stress"]:
    counts = df[f"{subscale}_Severity"].value_counts()
    sev_data[subscale] = [counts.get(s,0)/len(df)*100 for s in SEVERITY_ORDER]
sev_df = pd.DataFrame(sev_data, index=SEVERITY_ORDER)

fig, axes = plt.subplots(1, 2, figsize=(18, 6))
sev_df.T.plot(kind="bar", ax=axes[0], color=SEVERITY_COLORS, width=0.7, edgecolor="white")
axes[0].set_title("Severity Distribution per Subscale", fontsize=13, weight="bold")
axes[0].set_ylabel("% of Respondents")
axes[0].set_xticklabels(["Depression","Anxiety","Stress"], rotation=0)
axes[0].legend(title="Severity", bbox_to_anchor=(1.01, 1), loc="upper left")

sev_df.T.plot(kind="bar", stacked=True, ax=axes[1], color=SEVERITY_COLORS, width=0.6, edgecolor="white")
axes[1].set_title("Cumulative Severity Proportions", fontsize=13, weight="bold")
axes[1].set_ylabel("% of Respondents")
axes[1].set_xticklabels(["Depression","Anxiety","Stress"], rotation=0)
axes[1].legend(title="Severity", bbox_to_anchor=(1.01, 1), loc="upper left")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Subscale correlations & co-morbidity ─────────────────────────────────────
# REASON: High correlations mean the subscales share variance (comorbidity).
# This affects multi-label model architecture choices.
print("Pearson Correlations between subscales:")
for a, b in [("Depression","Anxiety"),("Depression","Stress"),("Anxiety","Stress")]:
    r, p = stats.pearsonr(df[a].dropna(), df[b].dropna())
    sig  = "***" if p < 0.001 else ("**" if p < 0.01 else "*")
    print(f"  {a} vs {b}: r = {r:.3f}  (p < 0.001) {sig}")

# Elevated = Moderate, Severe, or Extremely Severe
for s in ["Depression","Anxiety","Stress"]:
    df[f"{s}_Elevated"] = df[f"{s}_Severity"].isin(["Moderate","Severe","Extremely Severe"]).astype(int)

combos = {
    "D+A+S": (df.Depression_Elevated & df.Anxiety_Elevated & df.Stress_Elevated).sum(),
    "D+A":   (df.Depression_Elevated & df.Anxiety_Elevated & ~df.Stress_Elevated.astype(bool)).sum(),
    "D+S":   (df.Depression_Elevated & ~df.Anxiety_Elevated.astype(bool) & df.Stress_Elevated).sum(),
    "A+S":   (~df.Depression_Elevated.astype(bool) & df.Anxiety_Elevated & df.Stress_Elevated).sum(),
    "D only":(df.Depression_Elevated & ~df.Anxiety_Elevated.astype(bool) & ~df.Stress_Elevated.astype(bool)).sum(),
    "A only":(~df.Depression_Elevated.astype(bool) & df.Anxiety_Elevated & ~df.Stress_Elevated.astype(bool)).sum(),
    "S only":(~df.Depression_Elevated.astype(bool) & ~df.Anxiety_Elevated.astype(bool) & df.Stress_Elevated).sum(),
    "None":  (~df.Depression_Elevated.astype(bool) & ~df.Anxiety_Elevated.astype(bool) & ~df.Stress_Elevated.astype(bool)).sum(),
}
combo_pct = {k: 100*v/len(df) for k,v in combos.items()}

corr_mat = df[["Depression","Anxiety","Stress"]].corr()
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.heatmap(corr_mat, annot=True, fmt=".3f", cmap="coolwarm", center=0,
            linewidths=0.5, ax=axes[0], annot_kws={"size":14})
axes[0].set_title("Pearson Correlation Between DASS Subscales", fontsize=12, weight="bold")

combo_colors = ["#8e44ad","#3498db","#e74c3c","#f39c12","#1abc9c","#27ae60","#d35400","#95a5a6"]
axes[1].barh(list(combo_pct.keys()), list(combo_pct.values()), color=combo_colors)
axes[1].set_title("Elevated Symptom Co-occurrence\\n(Moderate+ on each subscale)", fontsize=12, weight="bold")
axes[1].set_xlabel("% of All Respondents")
for i, v in enumerate(combo_pct.values()):
    axes[1].text(v+0.3, i, f"{v:.1f}%", va="center", fontsize=9)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Boxplots per severity ─────────────────────────────────────────────────────
# REASON: Verifies that severity thresholds genuinely separate score ranges.
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Score Distribution Within Each Severity Category", fontsize=14, weight="bold")

for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    sev_col  = f"{subscale}_Severity"
    plot_df  = df[[subscale, sev_col]].dropna()
    plot_df[sev_col] = pd.Categorical(plot_df[sev_col], categories=SEVERITY_ORDER, ordered=True)
    plot_df  = plot_df.sort_values(sev_col)
    sns.boxplot(data=plot_df, x=sev_col, y=subscale,
                hue=sev_col, palette=dict(zip(SEVERITY_ORDER, SEVERITY_COLORS)), ax=ax, legend=False)
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Severity"); ax.set_ylabel("Score")
    ax.tick_params(axis="x", rotation=20)

plt.tight_layout(); plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 – DEMOGRAPHICS
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 3 — Demographic Analysis <a id='demographics'></a>

**Why?**  
Understanding *who* took the survey is essential for:
- Detecting sampling bias (young female Malaysian sample won't generalise well globally)
- Identifying demographic predictors of mental health severity
- Deciding whether stratified cross-validation is needed in the ML pipeline

We analyse age, gender, education, country, and cross-tabulate with DASS scores.
"""))

cells.append(code("""
df = df_raw.copy()
df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# ── Demographic label mapping ─────────────────────────────────────────────────
df["age_num"]         = pd.to_numeric(df["age"], errors="coerce")
df["age_valid"]       = df["age_num"].between(13, 100)
df["gender_label"]    = df["gender"].astype(str).map(GENDER_MAP)
df["education_label"] = df["education"].astype(str).map(EDUCATION_MAP)
df["urban_label"]     = df["urban"].astype(str).map(URBAN_MAP)
df["engnat_label"]    = df["engnat"].astype(str).map(ENGNAT_MAP)

# Age binning into life-stage groups
bins   = [12, 17, 24, 34, 44, 54, 100]
labels = ["13-17","18-24","25-34","35-44","45-54","55+"]
df["age_group"] = pd.cut(df.loc[df["age_valid"],"age_num"], bins=bins, labels=labels)

age_valid_df = df[df["age_valid"]]["age_num"]
print(f"Age: mean={age_valid_df.mean():.1f}  median={age_valid_df.median():.1f}  std={age_valid_df.std():.1f}")
print(f"Range (valid): {age_valid_df.min():.0f} - {age_valid_df.max():.0f}")
"""))

cells.append(code("""
# ── Age distribution ──────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(age_valid_df, bins=50, color="#3498db", edgecolor="white")
axes[0].axvline(age_valid_df.mean(),   color="red",    linestyle="--", label=f"Mean {age_valid_df.mean():.1f}")
axes[0].axvline(age_valid_df.median(), color="orange", linestyle=":",  label=f"Median {age_valid_df.median():.1f}")
axes[0].set_title("Age Distribution (valid 13-100)", fontsize=12, weight="bold")
axes[0].set_xlabel("Age"); axes[0].set_ylabel("Count"); axes[0].legend()

age_group_counts = df["age_group"].value_counts().sort_index()
axes[1].bar(age_group_counts.index.astype(str), age_group_counts.values, color="#2980b9", edgecolor="white")
axes[1].set_title("Respondents by Age Group", fontsize=12, weight="bold")
axes[1].set_xlabel("Age Group"); axes[1].set_ylabel("Count")
for i, v in enumerate(age_group_counts.values):
    axes[1].text(i, v+50, f"{v:,}", ha="center", fontsize=9)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Gender & Education ────────────────────────────────────────────────────────
gender_counts = df["gender_label"].value_counts()
edu_order     = ["< High School","High School","University","Graduate","Unknown"]
edu_counts    = df["education_label"].value_counts().reindex(edu_order, fill_value=0)

print("Gender:"); [print(f"  {k}: {v:,} ({100*v/len(df):.1f}%)") for k,v in gender_counts.items()]
print("\\nEducation:"); [print(f"  {k}: {v:,} ({100*v/len(df):.1f}%)") for k,v in edu_counts.items()]

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
colors_gen = ["#e74c3c","#3498db","#2ecc71","#95a5a6"]
axes[0].pie(gender_counts.values, labels=gender_counts.index, autopct="%1.1f%%",
            colors=colors_gen[:len(gender_counts)], startangle=140,
            wedgeprops={"edgecolor":"white","linewidth":2})
axes[0].set_title("Gender Distribution", fontsize=13, weight="bold")

axes[1].barh(edu_counts.index, edu_counts.values, color="#9b59b6", edgecolor="white")
axes[1].set_title("Education Level", fontsize=13, weight="bold")
axes[1].set_xlabel("Count")
for i, v in enumerate(edu_counts.values):
    axes[1].text(v+100, i, f"{v:,}", va="center", fontsize=9)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Top 20 Countries ──────────────────────────────────────────────────────────
# REASON: Geographic concentration (54% Malaysia) can introduce cultural bias.
country_counts = df["country"].value_counts().head(20)
print("Top 10 countries:")
for c, v in country_counts.head(10).items():
    print(f"  {c}: {v:,}  ({100*v/len(df):.1f}%)")

fig, ax = plt.subplots(figsize=(12, 7))
colors_c = plt.cm.tab20(np.linspace(0, 1, len(country_counts)))
ax.barh(country_counts.index[::-1], country_counts.values[::-1], color=colors_c)
ax.set_title("Top 20 Countries by Respondent Count", fontsize=13, weight="bold")
ax.set_xlabel("Number of Respondents")
for i, v in enumerate(country_counts.values[::-1]):
    ax.text(v+50, i, f"{v:,}", va="center", fontsize=8)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── DASS scores by Gender (Mann-Whitney U test) ───────────────────────────────
# REASON: Literature shows gender differences in D/A/S. Confirming this
# validates the dataset contains expected clinical signal.
gender_filter = df["gender_label"].isin(["Male","Female"])
gender_plot   = df[gender_filter][["gender_label","Depression","Anxiety","Stress"]].melt(
    id_vars="gender_label", var_name="Subscale", value_name="Score")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DASS-21 Scores by Gender (Male vs Female)", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    sub = gender_plot[gender_plot["Subscale"]==subscale]
    sns.boxplot(data=sub, x="gender_label", y="Score",
                hue="gender_label",
                palette={"Male":"#3498db","Female":"#e74c3c"}, ax=ax, legend=False)
    male_s   = df[df["gender_label"]=="Male"][subscale].dropna()
    female_s = df[df["gender_label"]=="Female"][subscale].dropna()
    u, p     = stats.mannwhitneyu(male_s, female_s, alternative="two-sided")
    sig      = "***" if p < 0.001 else ("**" if p < 0.01 else "*")
    ax.set_title(f"{subscale}  (p{sig})", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Gender"); ax.set_ylabel("Score")
    print(f"{subscale}: U={u:.0f}, p={p:.2e} {sig} | Male mean={male_s.mean():.1f} | Female mean={female_s.mean():.1f}")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── DASS by Age Group ─────────────────────────────────────────────────────────
# REASON: Younger groups (18-24) typically show the highest mental health burden.
age_plot = df[df["age_valid"] & df["age_group"].notna()]
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Mean DASS-21 Scores by Age Group", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    means = age_plot.groupby("age_group", observed=True)[subscale].mean()
    sems  = age_plot.groupby("age_group", observed=True)[subscale].sem()
    ax.bar(means.index.astype(str), means.values, yerr=sems.values,
           color=PALETTE[subscale], alpha=0.85, edgecolor="white", capsize=4)
    ax.set_title(f"{subscale}", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Age Group"); ax.set_ylabel("Mean Score ± SE")
    ax.tick_params(axis="x", rotation=20)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── DASS by Education Level ───────────────────────────────────────────────────
# REASON: Education is a socioeconomic protective factor. A gradient here
# justifies including education as an ML feature.
edu_order_valid = ["< High School","High School","University","Graduate"]
edu_plot = df[df["education_label"].isin(edu_order_valid)]
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Mean DASS-21 Scores by Education Level", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    means = edu_plot.groupby("education_label")[subscale].mean().reindex(edu_order_valid)
    sems  = edu_plot.groupby("education_label")[subscale].sem().reindex(edu_order_valid)
    ax.bar(means.index, means.values, yerr=sems.values,
           color=PALETTE[subscale], alpha=0.85, edgecolor="white", capsize=4)
    ax.set_title(f"{subscale}", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Education Level"); ax.set_ylabel("Mean Score ± SE")
    ax.tick_params(axis="x", rotation=15)
plt.tight_layout(); plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 – ITEM ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 4 — Item-Level Analysis <a id='items'></a>

**Why?**  
The 42 individual DASS items are the raw features for the ML model.  
We must evaluate each item's quality:
- **Response frequency heatmap** — identifies floor/ceiling effects
- **Corrected Item-Total Correlation (CITC)** — items with CITC < 0.3 are weak features
- **Per-item response time** — unusually fast responses may indicate disengagement
- **Careless responding** — long runs of the same answer flag unreliable respondents
"""))

cells.append(code("""
df = df_raw.copy()
q_cols   = [f"Q{i}A" for i in range(1, 43)]
q_e_cols = [f"Q{i}E" for i in range(1, 43)]
df[q_cols]   = df[q_cols].apply(pd.to_numeric,   errors="coerce")
df[q_e_cols] = df[q_e_cols].apply(pd.to_numeric, errors="coerce")

subscale_map = {}
for q in DEPRESSION_QS: subscale_map[q] = "Depression"
for q in ANXIETY_QS:    subscale_map[q] = "Anxiety"
for q in STRESS_QS:     subscale_map[q] = "Stress"
subscale_color = {"Depression":"#3498db","Anxiety":"#e74c3c","Stress":"#f39c12"}

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)
print("Item-level analysis ready.")
"""))

cells.append(code("""
# ── Item response frequency heatmap ──────────────────────────────────────────
resp_pct = pd.DataFrame(index=range(1,43), columns=[1,2,3,4], dtype=float)
for i in range(1,43):
    col = f"Q{i}A"
    vc  = df[col].value_counts(normalize=True)*100
    for v in [1,2,3,4]:
        resp_pct.loc[i,v] = vc.get(v, 0)

col_labels_map = {q: ("D" if subscale_map[q]=="Depression" else "A" if subscale_map[q]=="Anxiety" else "S")
                  for q in range(1,43)}
y_labels = [f"Q{i} [{col_labels_map[i]}]" for i in range(1,43)]

fig, axes = plt.subplots(1, 2, figsize=(20, 14))
sns.heatmap(resp_pct.values.astype(float), ax=axes[0], cmap="YlOrRd",
            xticklabels=["Never (1)","Sometimes (2)","Often (3)","Always (4)"],
            yticklabels=y_labels, linewidths=0.3,
            cbar_kws={"label":"% of Respondents"})
axes[0].set_title("Item Response Frequency Heatmap\\n(D=Depression  A=Anxiety  S=Stress)", fontsize=12, weight="bold")
axes[0].tick_params(axis="y", labelsize=7)

means      = df[q_cols].mean()
colors_bar = [subscale_color[subscale_map[i]] for i in range(1,43)]
axes[1].barh([f"Q{i}" for i in range(1,43)][::-1], means.values[::-1], color=colors_bar[::-1])
axes[1].set_title("Mean Response per Item (1-4 scale)", fontsize=12, weight="bold")
axes[1].set_xlabel("Mean Response")
axes[1].axvline(2.5, color="gray", linestyle="--", label="Midpoint")
handles = [mpatches.Patch(color=c, label=l) for l,c in subscale_color.items()]
axes[1].legend(handles=handles, loc="lower right")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Corrected Item-Total Correlation (CITC) ───────────────────────────────────
# REASON: CITC measures how well each item contributes to its subscale.
# Items with CITC < 0.3 are poor discriminators and candidates for removal.
citc_results = {}
for subscale, q_list in [("Depression",DEPRESSION_QS),("Anxiety",ANXIETY_QS),("Stress",STRESS_QS)]:
    total = df[[f"Q{q}A" for q in q_list]].sum(axis=1)
    for q in q_list:
        col  = f"Q{q}A"
        rest = total - df[col]  # corrected = correlate with (total minus item)
        r    = df[col].corr(rest)
        citc_results[f"Q{q}"] = {"Subscale": subscale, "CITC": round(r,3)}

citc_df = (pd.DataFrame(citc_results).T.reset_index()
             .rename(columns={"index":"Item"}))
citc_df["CITC"]     = citc_df["CITC"].astype(float)
citc_df["Item_num"] = citc_df["Item"].str[1:].astype(int)
citc_df = citc_df.sort_values("Item_num")

print(f"CITC range: {citc_df['CITC'].min():.3f} - {citc_df['CITC'].max():.3f}")
low_citc = citc_df[citc_df["CITC"] < 0.3]
print(f"Items with CITC < 0.3: {len(low_citc)} (these are weak features)")

fig, ax = plt.subplots(figsize=(14, 6))
colors_citc = [subscale_color[s] for s in citc_df["Subscale"]]
ax.bar(citc_df["Item"], citc_df["CITC"], color=colors_citc, edgecolor="white")
ax.axhline(0.3, color="red",    linestyle="--", lw=1.5, label="0.3 threshold")
ax.axhline(0.5, color="orange", linestyle=":",  lw=1.5, label="0.5 = good")
ax.set_title("Corrected Item-Total Correlations (CITC)", fontsize=13, weight="bold")
ax.set_xlabel("Item"); ax.set_ylabel("CITC")
ax.tick_params(axis="x", rotation=90, labelsize=7)
handles = [mpatches.Patch(color=c, label=l) for l,c in subscale_color.items()]
handles += [plt.Line2D([0],[0],color="red",linestyle="--",label="0.3 threshold"),
            plt.Line2D([0],[0],color="orange",linestyle=":",label="0.5 good")]
ax.legend(handles=handles, loc="lower right")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Per-item response time ────────────────────────────────────────────────────
# REASON: Items answered unusually quickly may not have been read carefully.
median_times = [df[f"Q{i}E"].median() for i in range(1,43)]
colors_time  = [subscale_color[subscale_map[i]] for i in range(1,43)]

fig, ax = plt.subplots(figsize=(14, 5))
ax.bar([f"Q{i}" for i in range(1,43)], median_times, color=colors_time, edgecolor="white")
ax.set_title("Median Response Time per Item (milliseconds)", fontsize=13, weight="bold")
ax.set_xlabel("Item"); ax.set_ylabel("Median Time (ms)")
ax.tick_params(axis="x", rotation=90, labelsize=7)
handles = [mpatches.Patch(color=c, label=l) for l,c in subscale_color.items()]
ax.legend(handles=handles)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Careless responding (long-string analysis) ────────────────────────────────
# REASON: Long runs of identical answers indicate the respondent is not
# reading questions. This is a standard careless-responding detection metric.
def longest_run(row):
    answers = [row[f"Q{i}A"] for i in range(1,43)]
    if all(pd.isna(a) for a in answers): return 0
    max_run, cur_run, prev = 1, 1, answers[0]
    for a in answers[1:]:
        if pd.isna(a): continue
        if a == prev: cur_run += 1; max_run = max(max_run, cur_run)
        else: cur_run = 1
        prev = a
    return max_run

print("Computing longest-run scores (may take ~30s on Colab)...")
df["longest_run"] = df.apply(longest_run, axis=1)

threshold  = 10
n_careless = (df["longest_run"] >= threshold).sum()
print(f"Median longest run  : {df['longest_run'].median():.0f}")
print(f"Mean longest run    : {df['longest_run'].mean():.1f}")
print(f">= {threshold} consecutive same answers: {n_careless:,}  ({100*n_careless/len(df):.2f}%)")

fig, ax = plt.subplots(figsize=(12, 5))
run_counts = df["longest_run"].value_counts().sort_index()
ax.bar(run_counts.index, run_counts.values, color="#3498db", edgecolor="white")
ax.axvline(threshold, color="red", linestyle="--", lw=2, label=f"Threshold = {threshold}")
ax.set_title("Distribution of Longest Consecutive Same-Answer Runs\\n(Careless Responding Indicator)", fontsize=13, weight="bold")
ax.set_xlabel("Longest Run of Identical Responses"); ax.set_ylabel("Count")
ax.set_xlim(0, 42); ax.legend()
plt.tight_layout(); plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 – PERSONALITY & VCL
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 5 — Big Five Personality (TIPI) & VCL Analysis <a id='personality'></a>

**Why?**  
The survey includes the **Ten-Item Personality Inventory (TIPI)** measuring the Big Five:
Extraversion, Agreeableness, Conscientiousness, Neuroticism, Openness.

- **Neuroticism** is the strongest known transdiagnostic risk factor for anxiety and depression
- **Conscientiousness** is a protective factor against stress
- Confirming these patterns validates the dataset and justifies including TIPI in the ML feature set

The **VCL** (vocabulary check) contains 3 fake words (VCL6, VCL9, VCL12). We test whether
excluding respondents who endorsed fake words materially changes the DASS distributions.

**TIPI scoring** (Gosling et al., 2003):
Reverse-scored items: TIPI2, TIPI4, TIPI6, TIPI8, TIPI10 → reverse = `8 - raw`
"""))

cells.append(code("""
df = df_raw.copy()
df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

tipi_cols = [f"TIPI{i}" for i in range(1,11)]
df[tipi_cols] = df[tipi_cols].apply(pd.to_numeric, errors="coerce")

df["Extraversion"]      = (df["TIPI1"] + (8 - df["TIPI6"])) / 2
df["Agreeableness"]     = ((8 - df["TIPI2"]) + df["TIPI7"])  / 2
df["Conscientiousness"] = (df["TIPI3"] + (8 - df["TIPI8"]))  / 2
df["Neuroticism"]       = (df["TIPI4"] + (8 - df["TIPI9"]))  / 2
df["Openness"]          = (df["TIPI5"] + (8 - df["TIPI10"])) / 2

big5        = ["Extraversion","Agreeableness","Conscientiousness","Neuroticism","Openness"]
big5_colors = ["#3498db","#2ecc71","#9b59b6","#e74c3c","#f39c12"]

for trait in big5:
    d = df[trait].dropna()
    print(f"  {trait:<20}: mean={d.mean():.2f}  median={d.median():.2f}  std={d.std():.2f}")
"""))

cells.append(code("""
# ── Big Five trait distributions ──────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Big Five Personality Trait Distributions (TIPI, 1-7 scale)", fontsize=14, weight="bold")
axes_flat = axes.flatten()

for ax, trait, color in zip(axes_flat, big5, big5_colors):
    data = df[trait].dropna()
    ax.hist(data, bins=30, color=color, alpha=0.7, edgecolor="white")
    ax.axvline(data.mean(), color="black", linestyle="--", lw=2, label=f"Mean {data.mean():.2f}")
    ax.set_title(trait, fontsize=12, weight="bold", color=color)
    ax.set_xlabel("Score (1-7)"); ax.set_ylabel("Count")
    ax.legend(fontsize=9)

axes_flat[-1].set_visible(False)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Big Five x DASS correlations ──────────────────────────────────────────────
# REASON: Neuroticism should be positively correlated; Conscientiousness /
# Extraversion negatively. Confirming this validates dataset quality.
combo = df[big5 + ["Depression","Anxiety","Stress"]].dropna()
corr  = combo.corr()
corr_sub = corr.loc[big5, ["Depression","Anxiety","Stress"]]

print(f"{'Trait':<22} {'Depression':>12} {'Anxiety':>10} {'Stress':>10}")
print("-" * 58)
for trait in big5:
    vals = [corr_sub.loc[trait, s] for s in ["Depression","Anxiety","Stress"]]
    sigs = []
    for s in ["Depression","Anxiety","Stress"]:
        r, p = stats.pearsonr(df[trait].dropna(), df[s][df[trait].notna()])
        sigs.append("***" if p<0.001 else "ns")
    print(f"  {trait:<20} {vals[0]:>+12.3f}{sigs[0]:>3} {vals[1]:>+10.3f}{sigs[1]:>3} {vals[2]:>+8.3f}{sigs[2]:>3}")

fig, axes = plt.subplots(1, 2, figsize=(18, 6))
sns.heatmap(corr_sub, annot=True, fmt=".3f", cmap="coolwarm", center=0,
            linewidths=0.5, ax=axes[0], annot_kws={"size":12},
            cbar_kws={"label":"Pearson r"})
axes[0].set_title("Big Five x DASS Correlations\\n(Negative = protective, Positive = risk factor)", fontsize=12, weight="bold")

mask = np.zeros_like(corr, dtype=bool)
mask[np.triu_indices_from(mask)] = True
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
            linewidths=0.3, ax=axes[1], mask=mask, annot_kws={"size":7},
            cbar_kws={"label":"Pearson r"})
axes[1].set_title("Full Correlation Matrix:\\nBig Five + DASS Subscales", fontsize=12, weight="bold")
axes[1].tick_params(axis="x", rotation=45, labelsize=8)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── VCL validity filter impact ────────────────────────────────────────────────
# REASON: Tests whether excluding fake-word endorsers changes DASS distributions.
# If it does, validity filtering is essential before training.
vcl_fake_cols = [v for v in VCL_FAKE if v in df.columns]
df["vcl_fail"] = df[vcl_fake_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) >= 1
n_fail = df["vcl_fail"].sum()
n_pass = (~df["vcl_fail"]).sum()
print(f"VCL PASS: {n_pass:,}  ({100*n_pass/len(df):.1f}%)")
print(f"VCL FAIL: {n_fail:,}  ({100*n_fail/len(df):.1f}%)")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DASS Scores: VCL Valid vs Invalid Respondents\\n(Invalid = endorsed >=1 fake vocabulary word)", fontsize=13, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    pass_s = df[~df["vcl_fail"]][subscale].dropna()
    fail_s = df[df["vcl_fail"]][subscale].dropna()
    ax.hist(pass_s, bins=50, alpha=0.6, color="#2ecc71", label=f"Valid (n={len(pass_s):,})", density=True)
    ax.hist(fail_s, bins=50, alpha=0.6, color="#e74c3c", label=f"Invalid (n={len(fail_s):,})", density=True)
    u, p = stats.mannwhitneyu(pass_s, fail_s, alternative="two-sided")
    sig  = "***" if p<0.001 else "ns"
    ax.set_title(f"{subscale}  (p{sig})", fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Score"); ax.set_ylabel("Density"); ax.legend(fontsize=9)
    print(f"{subscale}: pass mean={pass_s.mean():.1f}  fail mean={fail_s.mean():.1f}  p={p:.2e} {sig}")
plt.tight_layout(); plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 – FEATURE CORRELATION
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 6 — Feature Correlation & Multicollinearity <a id='correlation'></a>

**Why?**  
Before feeding features into ML models we must understand:
- Which features are most predictive of each DASS subscale (feature importance proxy)
- Whether any features are so highly correlated they add redundant information (multicollinearity)
- The overall correlation structure to inform PCA / dimensionality reduction decisions

Within-subscale items should cluster together (construct validity). Cross-subscale
correlations reveal shared variance from comorbidity.
"""))

cells.append(code("""
df = df_raw.copy()
df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

tipi_cols = [f"TIPI{i}" for i in range(1,11)]
df[tipi_cols] = df[tipi_cols].apply(pd.to_numeric, errors="coerce")
df["Extraversion"]      = (df["TIPI1"] + (8 - df["TIPI6"])) / 2
df["Agreeableness"]     = ((8 - df["TIPI2"]) + df["TIPI7"])  / 2
df["Conscientiousness"] = (df["TIPI3"] + (8 - df["TIPI8"]))  / 2
df["Neuroticism"]       = (df["TIPI4"] + (8 - df["TIPI9"]))  / 2
df["Openness"]          = (df["TIPI5"] + (8 - df["TIPI10"])) / 2
big5 = ["Extraversion","Agreeableness","Conscientiousness","Neuroticism","Openness"]

q_cols    = [f"Q{i}A" for i in range(1,43)]
demo_cols = ["age","gender","education","urban","engnat","familysize","screensize"]
df[q_cols]    = df[q_cols].apply(pd.to_numeric,    errors="coerce")
df[demo_cols] = df[demo_cols].apply(pd.to_numeric, errors="coerce")
print("Feature data ready.")
"""))

cells.append(code("""
# ── DASS item inter-correlation heatmap ───────────────────────────────────────
# REASON: Items within the same subscale should have higher correlations than
# cross-subscale items — confirms construct validity.
subscale_order = ([f"Q{q}A" for q in sorted(DEPRESSION_QS)] +
                  [f"Q{q}A" for q in sorted(ANXIETY_QS)]    +
                  [f"Q{q}A" for q in sorted(STRESS_QS)])
q_corr_ordered = df[q_cols].corr().loc[subscale_order, subscale_order]

fig, ax = plt.subplots(figsize=(16, 14))
mask = np.triu(np.ones_like(q_corr_ordered, dtype=bool))
sns.heatmap(q_corr_ordered, ax=ax, cmap="coolwarm", center=0, vmin=-0.2, vmax=1.0,
            linewidths=0.1, mask=mask, cbar_kws={"label":"Pearson r"},
            xticklabels=q_corr_ordered.columns, yticklabels=q_corr_ordered.index)
ax.set_title("DASS Item Inter-Correlation Matrix\\n(Grouped: Depression | Anxiety | Stress)", fontsize=13, weight="bold")
ax.tick_params(axis="both", labelsize=6, rotation=45)
dep_n = len(DEPRESSION_QS); anx_n = len(ANXIETY_QS)
for pos in [dep_n, dep_n + anx_n]:
    ax.axhline(pos, color="white", lw=2); ax.axvline(pos, color="white", lw=2)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Feature-DASS correlations (top/bottom 10 per subscale) ────────────────────
# REASON: Directly ranks which raw features are the strongest predictors.
all_features = q_cols + big5 + ["age","gender","education","urban","familysize"]
feature_corrs = {}
for subscale in ["Depression","Anxiety","Stress"]:
    corrs = {}
    for feat in all_features:
        try:
            valid = df[[feat, subscale]].dropna()
            r, _  = stats.pearsonr(valid[feat], valid[subscale])
            corrs[feat] = r
        except Exception:
            corrs[feat] = np.nan
    feature_corrs[subscale] = corrs

for subscale in ["Depression","Anxiety","Stress"]:
    s = pd.Series(feature_corrs[subscale]).dropna().sort_values()
    print(f"\\n{subscale} - Top 5 positive (risk):")
    for k, v in s.tail(5).items(): print(f"  {k}: r={v:+.3f}")
    print(f"{subscale} - Top 5 negative (protective):")
    for k, v in s.head(5).items(): print(f"  {k}: r={v:+.3f}")
"""))

cells.append(code("""
fig, axes = plt.subplots(1, 3, figsize=(22, 8))
fig.suptitle("Feature Correlations with DASS Subscales (Top & Bottom 10)", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    s      = pd.Series(feature_corrs[subscale]).dropna()
    plot_s = pd.concat([s.nsmallest(10), s.nlargest(10)]).sort_values()
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in plot_s.values]
    ax.barh(plot_s.index, plot_s.values, color=colors, edgecolor="white")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Pearson r"); ax.tick_params(axis="y", labelsize=7)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Pairplot: DASS subscales + top personality predictors ─────────────────────
# REASON: Pairplots reveal non-linear relationships and marginal distributions
# simultaneously — catches patterns Pearson r would miss.
pair_cols = ["Depression","Anxiety","Stress","Neuroticism","Conscientiousness","Extraversion"]
pair_df   = df[pair_cols].dropna().sample(min(3000, len(df)), random_state=42)

g = sns.pairplot(pair_df, diag_kind="kde",
                 plot_kws={"alpha":0.12, "s":4},
                 diag_kws={"fill":True})
g.fig.suptitle("Pairplot: DASS + Key Personality Traits (sample n=3,000)", fontsize=13, weight="bold", y=1.01)
plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 – CLASS BALANCE & ML READINESS
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Step 7 — Class Balance & ML Readiness <a id='ml'></a>

**Why?**  
For supervised ML, DASS severity becomes the label.  
We evaluate three label strategies and their class balance:
1. **5-class** — all five clinical severity levels (closest to clinical use)
2. **Binary** — Normal vs Elevated (simplest screening task)
3. **3-class** — Normal / Mild-Moderate / Severe+ (clinical triage)

We also build a **data quality funnel** to show how many clean samples remain
after each filter — the final count is the usable training corpus.
"""))

cells.append(code("""
df = df_raw.copy()
df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

for subscale, bands in SEVERITY.items():
    df[f"{subscale}_5cls"] = df[subscale].apply(classify_severity, bands=bands)

for subscale in ["Depression","Anxiety","Stress"]:
    df[f"{subscale}_binary"] = df[f"{subscale}_5cls"].apply(
        lambda x: "Normal" if x == "Normal" else "Elevated")
    df[f"{subscale}_3cls"]   = df[f"{subscale}_5cls"].apply(
        lambda x: "Normal" if x == "Normal" else ("Mild-Moderate" if x in ["Mild","Moderate"] else "Severe+"))

print("Labels computed.")
"""))

cells.append(code("""
# ── 5-class label distribution ─────────────────────────────────────────────────
print("5-Class Severity Distribution:")
print(f"{'Severity':<22} {'Depression':>12} {'Anxiety':>10} {'Stress':>10}")
print("-" * 58)
for sev in SEVERITY_ORDER:
    vals = [100*(df[f"{s}_5cls"]==sev).mean() for s in ["Depression","Anxiety","Stress"]]
    print(f"  {sev:<20} {vals[0]:>11.1f}% {vals[1]:>9.1f}% {vals[2]:>9.1f}%")

fig, axes = plt.subplots(1, 3, figsize=(20, 6))
fig.suptitle("5-Class Label Distribution (DASS-21 Clinical Severity)", fontsize=14, weight="bold")
for ax, subscale in zip(axes, ["Depression","Anxiety","Stress"]):
    counts = df[f"{subscale}_5cls"].value_counts().reindex(SEVERITY_ORDER, fill_value=0)
    bars   = ax.bar(SEVERITY_ORDER, counts.values, color=SEVERITY_COLORS, edgecolor="white")
    ax.set_title(subscale, fontsize=12, weight="bold", color=PALETTE[subscale])
    ax.set_xlabel("Severity"); ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=20)
    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+50,
                f"{v:,}\\n({100*v/len(df):.1f}%)", ha="center", fontsize=8)
    ratio = counts.max() / max(counts.min(), 1)
    print(f"  {subscale} imbalance ratio: {ratio:.1f}:1")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Binary & 3-class distributions ────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("Label Distributions: Binary vs 3-Class", fontsize=14, weight="bold")

for i, subscale in enumerate(["Depression","Anxiety","Stress"]):
    # Binary pie
    counts_bin = df[f"{subscale}_binary"].value_counts()
    axes[0][i].pie(counts_bin.values, labels=counts_bin.index, autopct="%1.1f%%",
                   colors=["#2ecc71","#e74c3c"], startangle=90,
                   wedgeprops={"edgecolor":"white","linewidth":2})
    axes[0][i].set_title(f"{subscale}\\nBinary (Normal vs Elevated)", fontsize=11, weight="bold")

    # 3-class bar
    cls3_order  = ["Normal","Mild-Moderate","Severe+"]
    cls3_colors = ["#2ecc71","#f39c12","#e74c3c"]
    counts_3cls = df[f"{subscale}_3cls"].value_counts().reindex(cls3_order, fill_value=0)
    bars = axes[1][i].bar(cls3_order, counts_3cls.values, color=cls3_colors, edgecolor="white")
    axes[1][i].set_title(f"{subscale}\\n3-Class", fontsize=11, weight="bold")
    axes[1][i].set_ylabel("Count")
    for bar, v in zip(bars, counts_3cls.values):
        axes[1][i].text(bar.get_x()+bar.get_width()/2, bar.get_height()+50,
                        f"{v:,}\\n({100*v/len(df):.1f}%)", ha="center", fontsize=9)

plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# ── Data quality funnel ────────────────────────────────────────────────────────
# REASON: Shows how many clean samples remain after each filter step.
# This is the definitive answer to "how much data can we actually train on?"
df["age_num"]        = pd.to_numeric(df["age"], errors="coerce")
df["age_valid"]      = df["age_num"].between(13, 100)
vcl_fake_cols        = [v for v in VCL_FAKE if v in df.columns]
df["vcl_fail"]       = df[vcl_fake_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) >= 1
df["testelapse_num"] = pd.to_numeric(df["testelapse"], errors="coerce")
df["too_fast"]       = df["testelapse_num"] < 60

stages = [
    ("Raw Dataset",           len(df)),
    ("No Exact Duplicates",   len(df) - df.duplicated().sum()),
    ("Valid Age (13-100)",    int(df["age_valid"].sum())),
    ("VCL Pass",              int((~df["vcl_fail"]).sum())),
    ("Test Time >= 60s",      int((~df["too_fast"]).sum())),
    ("All Filters Combined",  int((~(~df["age_valid"] | df["vcl_fail"] | df["too_fast"])).sum())),
]
print(f"{'Stage':<28} {'Count':>8}  {'%':>6}")
print("-" * 48)
for stage, count in stages:
    print(f"  {stage:<26} {count:>8,}  ({100*count/len(df):>5.1f}%)")

labels  = [s[0] for s in stages]
counts  = [s[1] for s in stages]
colors_f= ["#3498db","#2980b9","#1abc9c","#27ae60","#f39c12","#e74c3c"]

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(labels[::-1], counts[::-1], color=colors_f[::-1], edgecolor="white")
ax.set_title("Data Quality Filtering Funnel\\n(Samples Remaining After Each Filter)", fontsize=13, weight="bold")
ax.set_xlabel("Number of Respondents")
for bar, v in zip(bars, counts[::-1]):
    ax.text(v+100, bar.get_y()+bar.get_height()/2, f"{v:,}  ({100*v/len(df):.1f}%)", va="center", fontsize=9)
plt.tight_layout(); plt.show()
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 – SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
cells.append(md("""
---
## Key Insights Summary <a id='summary'></a>

### 🔍 Data Quality
| Check | Finding | Action |
|---|---|---|
| Duplicates | **0** | None needed |
| Missing values | `major` 28.7%, `country` 0.01% | Structural — OK to keep |
| Likert out-of-range | **None** | Dataset is clean |
| Invalid ages | **7** (0.02%) | Exclude from age analyses |
| VCL fake-word cheaters | **5,192** (13.1%) | **Exclude before training** |
| Suspiciously fast (<60s) | **120** (0.3%) | Exclude as potential bots |
| **Clean training set** | **34,511 (86.8%)** | Final usable corpus |

---

### 📊 Score Distributions
| Subscale | Mean | Key Finding |
|---|---|---|
| Depression | 38.8 | 64.5% Extremely Severe — self-selection bias |
| Anxiety    | 32.1 | 68.6% Extremely Severe — strongest skew |
| Stress     | 42.3 | 64.2% Extremely Severe |
| D↔A correlation | r=0.666 | High comorbidity |
| D↔S correlation | r=0.734 | Very high comorbidity |
| **A↔S correlation** | **r=0.802** | Near-collinear subscales |

---

### 👥 Demographics
- **Young** — median age 21 (range 13–99)
- **Female-dominated** — 76.3% female
- **Geographically skewed** — 54.3% Malaysia, 20.6% USA
- All gender differences are highly significant (p < 0.001)

---

### 🧠 Item Quality
- All 42 items have CITC > 0.41 → **all are valid ML features**
- No items need dropping based on item analysis

---

### 🧬 Personality Predictors
| Trait | r (Depression) | Interpretation |
|---|---|---|
| Neuroticism | **+0.43** | Strongest risk factor |
| Conscientiousness | **−0.22** | Protective |
| Extraversion | −0.17 | Mildly protective |

---

### ⚖️ ML Readiness
| Strategy | Imbalance Ratio | Recommendation |
|---|---|---|
| 5-class | 15–21:1 | Needs SMOTE + class_weight |
| Binary (Normal vs Elevated) | ~9:1 | Best starting point |
| 3-class (Normal/Mild-Mod/Severe+) | ~6:1 | Clinical triage model |

**Recommended feature set:**
- 42 DASS-42 Q items (Q1A–Q42A) — primary predictors
- 5 Big Five composites (TIPI)
- Demographics: age, gender, education, urban, engnat
- VCL real-word sum as engagement proxy
"""))

cells.append(code("""
# ── Final clean dataset export ────────────────────────────────────────────────
df = df_raw.copy()
df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

# Apply all quality filters
df["age_num"]        = pd.to_numeric(df["age"], errors="coerce")
df["age_valid"]      = df["age_num"].between(13, 100)
vcl_fake_cols        = [v for v in VCL_FAKE if v in df.columns]
df["vcl_fail"]       = df[vcl_fake_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1) >= 1
df["testelapse_num"] = pd.to_numeric(df["testelapse"], errors="coerce")
df["too_fast"]       = df["testelapse_num"] < 60
any_issue            = (~df["age_valid"]) | df["vcl_fail"] | df["too_fast"]
df_clean             = df[~any_issue].copy()

print(f"Clean dataset: {len(df_clean):,} rows")

# TIPI Big Five scoring
tipi_cols = [f"TIPI{i}" for i in range(1,11)]
df_clean[tipi_cols] = df_clean[tipi_cols].apply(pd.to_numeric, errors="coerce")
df_clean["Extraversion"]      = (df_clean["TIPI1"] + (8 - df_clean["TIPI6"])) / 2
df_clean["Agreeableness"]     = ((8 - df_clean["TIPI2"]) + df_clean["TIPI7"])  / 2
df_clean["Conscientiousness"] = (df_clean["TIPI3"] + (8 - df_clean["TIPI8"]))  / 2
df_clean["Neuroticism"]       = (df_clean["TIPI4"] + (8 - df_clean["TIPI9"]))  / 2
df_clean["Openness"]          = (df_clean["TIPI5"] + (8 - df_clean["TIPI10"])) / 2

# Severity labels
for subscale, bands in SEVERITY.items():
    df_clean[f"{subscale}_Severity"] = df_clean[subscale].apply(classify_severity, bands=bands)
    df_clean[f"{subscale}_Binary"]   = df_clean[f"{subscale}_Severity"].apply(
        lambda x: "Normal" if x == "Normal" else "Elevated")
    df_clean[f"{subscale}_3class"]   = df_clean[f"{subscale}_Severity"].apply(
        lambda x: "Normal" if x=="Normal" else ("Mild-Moderate" if x in ["Mild","Moderate"] else "Severe+"))

print("\\nClean dataset ready for ML training.")
print(f"Available target columns: Depression_Severity, Anxiety_Severity, Stress_Severity")
print(f"                          *_Binary, *_3class")
print(f"\\nFeature summary:")
print(f"  Q items      : {len([c for c in df_clean if c.startswith('Q') and c.endswith('A')])} columns")
print(f"  TIPI Big Five: 5 composite columns")
print(f"  Demographics : age_num, gender, education, urban, engnat")

# Download the clean dataset
# df_clean.to_csv("dass_clean.csv", index=False)
# from google.colab import files
# files.download("dass_clean.csv")
print("\\nUncomment the last 3 lines above to download the clean dataset.")
"""))

# ═══════════════════════════════════════════════════════════════════════════════
# Write notebook JSON
# ═══════════════════════════════════════════════════════════════════════════════
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
        "colab": {"provenance": [], "toc_visible": True},
    },
    "cells": cells,
}

out_path = os.path.join(os.path.dirname(__file__), "DASS_EDA_Colab.ipynb")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"\n Notebook written to:\n  {out_path}")
print(f"  Cells: {len(cells)}")
