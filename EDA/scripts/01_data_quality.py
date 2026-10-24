"""
01_data_quality.py
==================
Step 1 – Data Quality Assessment

PURPOSE & REASON:
  Before any analysis, we must understand what we're working with.
  Data quality issues (missing values, duplicates, out-of-range responses,
  invalid ages, fake-word traps) can silently distort every downstream result.
  This script:
    1. Loads the raw TSV file and reports shape, dtypes, memory usage.
    2. Audits missing values per column.
    3. Detects duplicate rows.
    4. Identifies out-of-range Likert responses (valid: 1–4).
    5. Flags implausible ages (< 13 or > 100).
    6. Applies the VCL validity filter (respondents who "know" fake words
       are likely clicking randomly and should be examined).
    7. Checks for suspiciously fast completions (bot / random-clicker risk).
    8. Writes a text quality report and saves diagnostic plots.

OUTPUT:
  outputs/reports/data_quality_report.txt
  outputs/figures/01_missing_values.png
  outputs/figures/01_response_time_distribution.png
  outputs/figures/01_vcl_validity.png
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config_loader import *   # noqa

import pandas as pd
import numpy  as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")

# ── 1. Load data ─────────────────────────────────────────────────────────────
print("[01] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)
print(f"     Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ── 2. Basic meta ─────────────────────────────────────────────────────────────
report_lines = []
def log(msg=""):
    print(msg)
    report_lines.append(msg)

log("=" * 70)
log("DASS EDA — Data Quality Report")
log("=" * 70)
log(f"\nDataset: {DATA_PATH}")
log(f"Rows   : {df.shape[0]:,}")
log(f"Columns: {df.shape[1]}")
log(f"Memory : {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

log("\n-- Column types -------------------------------------------------------")
dtype_counts = df.dtypes.astype(str).value_counts()
for dtype_name, count in dtype_counts.items():
    log(f"  {str(dtype_name):<15}: {count} columns")

# ── 3. Missing values ─────────────────────────────────────────────────────────
# REASON: Missing values can bias summary statistics.  We separate
# structural missingness (e.g., 'major' only filled by graduates) from
# data-collection errors.
log("\n── Missing values ───────────────────────────────────────────────────────")
miss = df.isnull().sum()
miss_pct = 100 * miss / len(df)
miss_df = pd.DataFrame({"Missing": miss, "Pct%": miss_pct.round(2)})
miss_df = miss_df[miss_df["Missing"] > 0].sort_values("Missing", ascending=False)
if miss_df.empty:
    log("  No missing values found.")
else:
    log(miss_df.to_string())

# Plot missing values
fig, ax = plt.subplots(figsize=(10, max(3, len(miss_df) * 0.4)))
if not miss_df.empty:
    miss_df["Pct%"].plot(kind="barh", ax=ax, color="#e74c3c")
    ax.set_xlabel("Missing %")
    ax.set_title("Missing Values by Column", fontsize=14, weight="bold")
    ax.axvline(5, color="orange", linestyle="--", label="5% threshold")
    ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "01_missing_values.png"), dpi=FIG_DPI)
plt.close()
log("  → Figure saved: 01_missing_values.png")

# ── 4. Duplicate rows ─────────────────────────────────────────────────────────
# REASON: Duplicate submissions inflate n and skew distributions.
n_dups = df.duplicated().sum()
log(f"\n── Duplicate rows ───────────────────────────────────────────────────────")
log(f"  Exact duplicates: {n_dups:,}  ({100*n_dups/len(df):.2f}%)")

# ── 5. Likert response range check ───────────────────────────────────────────
# REASON: Valid DASS responses are 1–4. Values outside this range indicate
# data corruption or encoding errors.
log("\n── Out-of-range Likert responses (valid: 1–4) ───────────────────────────")
q_answer_cols = [f"Q{i}A" for i in range(1, 43)]
for col in q_answer_cols:
    if col in df.columns:
        bad = df[~df[col].isin([1, 2, 3, 4]) & df[col].notna()]
        if len(bad) > 0:
            log(f"  {col}: {len(bad)} out-of-range values → unique={sorted(bad[col].unique())}")
log("  (no output above = all responses in range 1–4)")

# ── 6. Age validity ───────────────────────────────────────────────────────────
# REASON: Some respondents entered their birth year or nonsense values.
# Ages below 13 (minimum realistic for online survey) and above 100 are
# treated as implausible.
log("\n── Age validity ─────────────────────────────────────────────────────────")
df["age_num"] = pd.to_numeric(df["age"], errors="coerce")
age_valid = df["age_num"].between(13, 100)
log(f"  Valid ages  (13–100): {age_valid.sum():,}  ({100*age_valid.mean():.2f}%)")
log(f"  Invalid ages        : {(~age_valid).sum():,}  ({100*(~age_valid).mean():.2f}%)")
log(f"  Age range (all)     : {df['age_num'].min():.0f} – {df['age_num'].max():.0f}")
log(f"  Age range (valid)   : {df.loc[age_valid,'age_num'].min():.0f} – {df.loc[age_valid,'age_num'].max():.0f}")

# ── 7. VCL Validity filter ────────────────────────────────────────────────────
# REASON: VCL6, VCL9, VCL12 are non-existent words.  A respondent who
# claims to know them is almost certainly clicking randomly.  This is a
# standard built-in validity check for this dataset.
log("\n── VCL Fake-word validity ────────────────────────────────────────────────")
for vcl in VCL_FAKE:
    if vcl in df.columns:
        checked = (df[vcl] == 1).sum()
        log(f"  {vcl} (fake word) checked as known: {checked:,}  ({100*checked/len(df):.2f}%)")

df["vcl_fail"] = df[[v for v in VCL_FAKE if v in df.columns]].sum(axis=1) >= 1
n_vcl_fail = df["vcl_fail"].sum()
log(f"  Respondents who checked ≥1 fake word: {n_vcl_fail:,}  ({100*n_vcl_fail/len(df):.2f}%)")

# Plot VCL validity
vcl_real_cols = [c for c in df.columns if c.startswith("VCL") and c not in VCL_FAKE]
vcl_data = pd.DataFrame({
    "Column": vcl_real_cols + VCL_FAKE,
    "Pct Checked": [100 * (df[c] == 1).mean() for c in vcl_real_cols + VCL_FAKE],
    "Type": ["Real"] * len(vcl_real_cols) + ["Fake"] * len(VCL_FAKE),
})
fig, ax = plt.subplots(figsize=(12, 5))
colors = vcl_data["Type"].map({"Real": "#3498db", "Fake": "#e74c3c"})
bars = ax.bar(vcl_data["Column"], vcl_data["Pct Checked"], color=colors)
ax.set_title("VCL Vocabulary Check — % Respondents Claiming Knowledge\n(Red = fake words; should be low)", fontsize=13, weight="bold")
ax.set_ylabel("% Checked")
ax.set_xlabel("VCL Item")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#3498db", label="Real Word"), Patch(color="#e74c3c", label="Fake Word")])
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "01_vcl_validity.png"), dpi=FIG_DPI)
plt.close()
log("  → Figure saved: 01_vcl_validity.png")

# ── 8. Response time analysis ─────────────────────────────────────────────────
# REASON: Extremely fast completions (< 1 min for 42 questions) suggest
# random clicking / bots.  We flag these as low-quality responses.
log("\n── Response-time sanity check ───────────────────────────────────────────")
df["testelapse_num"] = pd.to_numeric(df["testelapse"], errors="coerce")
MIN_VALID_SECS = 60   # 42 questions in < 60 sec → ~1.4 sec/question → suspect
too_fast = (df["testelapse_num"] < MIN_VALID_SECS).sum()
log(f"  Median test time   : {df['testelapse_num'].median():.0f} s  ({df['testelapse_num'].median()/60:.1f} min)")
log(f"  Mean test time     : {df['testelapse_num'].mean():.0f} s  ({df['testelapse_num'].mean()/60:.1f} min)")
log(f"  < 60 s (suspect)   : {too_fast:,}  ({100*too_fast/len(df):.2f}%)")

# Cap at 95th percentile for readability
p95 = df["testelapse_num"].quantile(0.95)
plot_times = df["testelapse_num"].clip(upper=p95).dropna()

fig, axes = plt.subplots(1, 2, figsize=FIG_SIZE)
axes[0].hist(plot_times, bins=80, color="#3498db", edgecolor="white")
axes[0].axvline(MIN_VALID_SECS, color="red", linestyle="--", label=f"60 s threshold")
axes[0].set_title("Distribution of Test Completion Times\n(clipped at 95th percentile)", fontsize=12, weight="bold")
axes[0].set_xlabel("Seconds")
axes[0].set_ylabel("Count")
axes[0].legend()

# Intro + survey elapse
df["introelapse_num"]   = pd.to_numeric(df["introelapse"],   errors="coerce")
df["surveyelapse_num"]  = pd.to_numeric(df["surveyelapse"],  errors="coerce")
time_summary = pd.DataFrame({
    "Phase": ["Intro", "Test (DASS)", "Survey (Demographics)"],
    "Median (s)": [df["introelapse_num"].median(),
                   df["testelapse_num"].median(),
                   df["surveyelapse_num"].median()],
})
axes[1].barh(time_summary["Phase"], time_summary["Median (s)"], color=["#9b59b6","#3498db","#2ecc71"])
axes[1].set_title("Median Time Spent per Survey Phase", fontsize=12, weight="bold")
axes[1].set_xlabel("Seconds")
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "01_response_time_distribution.png"), dpi=FIG_DPI)
plt.close()
log("  → Figure saved: 01_response_time_distribution.png")

# ── 9. Quality summary ────────────────────────────────────────────────────────
log("\n── Quality summary ──────────────────────────────────────────────────────")
log(f"  Total respondents            : {len(df):,}")
log(f"  Exact duplicates             : {n_dups:,}")
log(f"  Invalid age                  : {(~age_valid).sum():,}")
log(f"  VCL cheaters (≥1 fake word)  : {n_vcl_fail:,}")
log(f"  Suspiciously fast (<60 s)    : {too_fast:,}")
# All issues
any_issue = (~age_valid) | df["vcl_fail"] | (df["testelapse_num"] < MIN_VALID_SECS)
log(f"  Any quality issue            : {any_issue.sum():,}  ({100*any_issue.mean():.1f}%)")
log(f"  Clean respondents            : {(~any_issue).sum():,}  ({100*(~any_issue).mean():.1f}%)")

# ── Save report ───────────────────────────────────────────────────────────────
report_path = os.path.join(OUT_REP, "data_quality_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print(f"\n[01] Report saved → {report_path}")
print("[01] DONE\n")
