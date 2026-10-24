"""
04_item_analysis.py
===================
Step 4 – Individual Item & Response Pattern Analysis

PURPOSE & REASON:
  The 42 individual DASS items are the raw features for ML.  We must:
    • Understand the response distribution for each item (ceiling/floor effects
      indicate items that don't discriminate well between respondents).
    • Measure item-total correlations: items poorly correlated with their
      subscale total are weak features.
    • Check whether respondents answer consistently (long streaks of the same
      answer = careless responding).
    • Visualise the average response time per item — very fast responses may
      indicate low engagement.

OUTPUT:
  outputs/figures/04_item_response_distribution.png
  outputs/figures/04_item_total_correlations.png
  outputs/figures/04_item_response_times.png
  outputs/figures/04_careless_responding.png
  outputs/reports/item_analysis_report.txt
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config_loader import *   # noqa

import pandas as pd
import numpy  as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns

sns.set_theme(style="whitegrid")

print("[04] Loading data …")
df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)

# ── Answer columns & subscale membership ──────────────────────────────────────
q_cols  = [f"Q{i}A" for i in range(1, 43)]
q_e_cols= [f"Q{i}E" for i in range(1, 43)]
df[q_cols]  = df[q_cols].apply(pd.to_numeric, errors="coerce")
df[q_e_cols]= df[q_e_cols].apply(pd.to_numeric, errors="coerce")

subscale_map = {}
for q in DEPRESSION_QS: subscale_map[q] = "Depression"
for q in ANXIETY_QS:    subscale_map[q] = "Anxiety"
for q in STRESS_QS:     subscale_map[q] = "Stress"
subscale_color = {"Depression": "#3498db", "Anxiety": "#e74c3c", "Stress": "#f39c12"}

# ── Subscale totals ───────────────────────────────────────────────────────────
def subscale_score(df, q_list):
    cols = [f"Q{q}A" for q in q_list]
    return (df[cols] - 1).sum(axis=1) * 2

df["Depression"] = subscale_score(df, DEPRESSION_QS)
df["Anxiety"]    = subscale_score(df, ANXIETY_QS)
df["Stress"]     = subscale_score(df, STRESS_QS)

lines = []
def log(m=""):
    print(m); lines.append(m)

log("=" * 60)
log("DASS EDA — Item Analysis Report")
log("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Item response frequency heatmap
# REASON: A heatmap of all 42 items × 4 response options shows at a glance
#         which items have floor/ceiling effects (all 1s or all 4s) —
#         such items add little discriminative power for ML.
# ═══════════════════════════════════════════════════════════════════════════════
resp_pct = pd.DataFrame(index=range(1, 43), columns=[1, 2, 3, 4], dtype=float)
for i in range(1, 43):
    col = f"Q{i}A"
    vc  = df[col].value_counts(normalize=True) * 100
    for v in [1, 2, 3, 4]:
        resp_pct.loc[i, v] = vc.get(v, 0)

fig, axes = plt.subplots(1, 2, figsize=(20, 14))

# Heatmap for response 4 (highest endorsement)
resp_arr = resp_pct.values.astype(float)   # shape (42, 4)
col_labels_map = {
    q: ("D" if subscale_map.get(q)=="Depression" else
        "A" if subscale_map.get(q)=="Anxiety" else "S")
    for q in range(1, 43)
}
y_labels = [f"Q{i} [{col_labels_map[i]}]" for i in range(1, 43)]

sns.heatmap(resp_arr, ax=axes[0], cmap="YlOrRd",
            xticklabels=["Never (1)","Sometimes (2)","Often (3)","Always (4)"],
            yticklabels=y_labels, linewidths=0.3,
            annot=False, cbar_kws={"label": "% of Respondents"})
axes[0].set_title("Item Response Frequency Heatmap\n(D=Depression  A=Anxiety  S=Stress)",
                  fontsize=12, weight="bold")
axes[0].tick_params(axis="y", labelsize=7)

# Mean response per item
means = df[q_cols].mean()
colors_bar = [subscale_color[subscale_map[i]] for i in range(1, 43)]
axes[1].barh([f"Q{i}" for i in range(1, 43)][::-1], means.values[::-1], color=colors_bar[::-1])
axes[1].set_title("Mean Response per Item (1–4 scale)", fontsize=12, weight="bold")
axes[1].set_xlabel("Mean Response")
axes[1].axvline(2.5, color="gray", linestyle="--", label="Midpoint")
axes[1].legend()
from matplotlib.patches import Patch
handles = [Patch(color=c, label=l) for l, c in subscale_color.items()]
axes[1].legend(handles=handles, loc="lower right")

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "04_item_response_distribution.png"), dpi=FIG_DPI, bbox_inches="tight")
plt.close()
print("  → Figure saved: 04_item_response_distribution.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Item–total correlations (corrected)
# REASON: Corrected item-total correlation (CITC) measures how well each item
#         contributes to its subscale.  Items with CITC < 0.3 are poor
#         discriminators and may be dropped in feature selection.
# ═══════════════════════════════════════════════════════════════════════════════
log("\n── Item–Total Correlations ──────────────────────────────────────────────")
citc_results = {}
for subscale, q_list in [("Depression", DEPRESSION_QS),
                          ("Anxiety",    ANXIETY_QS),
                          ("Stress",     STRESS_QS)]:
    total = df[[f"Q{q}A" for q in q_list]].sum(axis=1)
    for q in q_list:
        col = f"Q{q}A"
        # corrected: correlation of item with (total − item)
        rest = total - df[col]
        r = df[col].corr(rest)
        citc_results[f"Q{q}"] = {"Subscale": subscale, "CITC": round(r, 3)}
        if r < 0.3:
            log(f"  LOW CITC: Q{q} ({subscale}) = {r:.3f}  ← consider dropping")

citc_df = pd.DataFrame(citc_results).T.reset_index().rename(columns={"index":"Item"})
citc_df["CITC"] = citc_df["CITC"].astype(float)
citc_df["Item_num"] = citc_df["Item"].str[1:].astype(int)
citc_df = citc_df.sort_values("Item_num")

fig, ax = plt.subplots(figsize=(14, 7))
colors_citc = [subscale_color[s] for s in citc_df["Subscale"]]
bars = ax.bar(citc_df["Item"], citc_df["CITC"], color=colors_citc, edgecolor="white")
ax.axhline(0.3, color="red", linestyle="--", linewidth=1.5, label="CITC = 0.3 threshold")
ax.axhline(0.5, color="orange", linestyle=":", linewidth=1.5, label="CITC = 0.5 good")
ax.set_title("Corrected Item-Total Correlations (CITC)\nby DASS-42 Item and Subscale", fontsize=13, weight="bold")
ax.set_xlabel("Item")
ax.set_ylabel("CITC")
ax.tick_params(axis="x", rotation=90, labelsize=7)
ax.legend()
handles = [Patch(color=c, label=l) for l, c in subscale_color.items()]
ax.legend(handles=handles + [plt.Line2D([0],[0], color="red",  linestyle="--", label="0.3 threshold"),
                              plt.Line2D([0],[0], color="orange", linestyle=":", label="0.5 good")],
          loc="lower right")
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "04_item_total_correlations.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 04_item_total_correlations.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 – Per-item response time
# REASON: Items answered unusually quickly may not have been read carefully.
#         Identifying these items guides data cleaning thresholds.
# ═══════════════════════════════════════════════════════════════════════════════
median_times = [df[f"Q{i}E"].median() for i in range(1, 43)]
colors_time  = [subscale_color[subscale_map[i]] for i in range(1, 43)]

fig, ax = plt.subplots(figsize=(14, 5))
ax.bar([f"Q{i}" for i in range(1, 43)], median_times, color=colors_time, edgecolor="white")
ax.set_title("Median Response Time per Item (milliseconds)", fontsize=13, weight="bold")
ax.set_xlabel("Item")
ax.set_ylabel("Median Response Time (ms)")
ax.tick_params(axis="x", rotation=90, labelsize=7)
handles = [Patch(color=c, label=l) for l, c in subscale_color.items()]
ax.legend(handles=handles)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "04_item_response_times.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 04_item_response_times.png")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 – Careless responding detection (long-string analysis)
# REASON: Respondents who select the same answer for many consecutive items
#         are likely not reading questions.  Longest run of identical answers
#         is a standard careless-responding metric.
# ═══════════════════════════════════════════════════════════════════════════════
def longest_run(row):
    answers = [row[f"Q{i}A"] for i in range(1, 43)]
    if all(pd.isna(a) for a in answers):
        return 0
    max_run, cur_run, prev = 1, 1, answers[0]
    for a in answers[1:]:
        if pd.isna(a):
            continue
        if a == prev:
            cur_run += 1
            max_run = max(max_run, cur_run)
        else:
            cur_run = 1
        prev = a
    return max_run

print("  Computing longest-run scores (may take a moment) …")
df["longest_run"] = df.apply(longest_run, axis=1)

log("\n── Careless Responding (Long-String Analysis) ───────────────────────────")
log(f"  Median longest run : {df['longest_run'].median():.0f}")
log(f"  Mean longest run   : {df['longest_run'].mean():.1f}")
threshold = 10
n_careless = (df["longest_run"] >= threshold).sum()
log(f"  ≥{threshold} consecutive same answers: {n_careless:,}  ({100*n_careless/len(df):.2f}%)")

fig, ax = plt.subplots(figsize=(12, 5))
run_counts = df["longest_run"].value_counts().sort_index()
ax.bar(run_counts.index, run_counts.values, color="#3498db", edgecolor="white")
ax.axvline(threshold, color="red", linestyle="--", linewidth=2, label=f"Threshold = {threshold}")
ax.set_title("Distribution of Longest Consecutive Same-Answer Runs\n(Careless Responding Indicator)",
             fontsize=13, weight="bold")
ax.set_xlabel("Longest Run of Identical Responses")
ax.set_ylabel("Number of Respondents")
ax.set_xlim(0, 42)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, "04_careless_responding.png"), dpi=FIG_DPI)
plt.close()
print("  → Figure saved: 04_careless_responding.png")

rep_path = os.path.join(OUT_REP, "item_analysis_report.txt")
with open(rep_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  → Report saved: {rep_path}")
print("[04] DONE\n")
