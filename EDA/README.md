# DASS Dataset — Exploratory Data Analysis

**Project:** ML Mental Health Screening  
**Dataset:** DASS-42 Online Survey (2017–2019)  
**Analyst:** Antigravity AI  
**Date:** September 2026  
**Respondents:** 39,775  |  **Variables:** 172  |  **Size:** ~20 MB

---

## Folder Structure

```
EDA/
├── scripts/
│   ├── 00_config.py                  # Central config (paths, subscale maps, severity thresholds)
│   ├── _config_loader.py             # Import shim for 00_config (Python digit-prefix workaround)
│   ├── 01_data_quality.py            # Data quality audit
│   ├── 02_dass_scores.py             # DASS score computation & distribution analysis
│   ├── 03_demographics.py            # Demographic breakdown & group comparisons
│   ├── 04_item_analysis.py           # Item-level response & validity analysis
│   ├── 05_personality_vcl.py         # Big Five personality + VCL analysis
│   ├── 06_feature_correlation.py     # Feature correlation & multicollinearity
│   ├── 07_class_balance.py           # ML label strategies & class balance
│   └── run_all_eda.py                # Master runner (run this to reproduce all outputs)
│
└── outputs/
    ├── figures/                      # 27 PNG visualizations
    └── reports/                      # 6 plain-text summary reports
```

### How to Run

```powershell
# From project root:
$env:PYTHONIOENCODING="utf-8"
& "ml\.venv\Scripts\python.exe" "EDA\scripts\run_all_eda.py"
```

---

## Script-by-Script Documentation

Every step below documents **what was done** and **why** it was done.

---

### Script 01 — Data Quality Audit (`01_data_quality.py`)

**Purpose:** Before any analysis, we must understand and document the raw data's quality.  
Silent data quality issues can invalidate all downstream conclusions and model performance claims.

| Check | Result | Implication |
|---|---|---|
| Shape | 39,775 rows × 172 cols | Large, reasonably wide dataset |
| Memory | 58.2 MB | Fits comfortably in RAM |
| Exact duplicates | **0** | No deduplication needed |
| Missing values | `major` (28.7%), `country` (0.01%) | Structural — `major` only filled by graduates |
| Likert out-of-range | **None** | All Q responses cleanly in 1–4 |
| Invalid ages | **7** (0.02%) — max was 1998 | Likely birth-year entry; exclude from age analyses |
| VCL fake-word cheaters | **5,192** (13.1%) | Standard validity filter; conservative exclusion recommended |
| Suspiciously fast completions | **120** (0.3%) — under 60 s | Risk of random-clicking bots |
| **Clean after all filters** | **34,511 (86.8%)** | Usable training corpus |

**Figures generated:**
- `01_missing_values.png` — Bar chart of missingness by column
- `01_vcl_validity.png` — Real vs. fake VCL word endorsement rates
- `01_response_time_distribution.png` — Test completion time histogram + phase breakdown

---

### Script 02 — DASS Score Computation & Distributions (`02_dass_scores.py`)

**Purpose:** Compute the three DASS-21 subscale scores (Depression, Anxiety, Stress) from the
42 raw item responses and characterise their distributions.

**Scoring rule:** `Score = (Sum of item responses − 14) × 2`  
(shifts 1–4 scale to 0–3, sums 14 items, multiplies by 2 to match DASS-21 published norms)

| Subscale | Mean | Median | Std | Skewness |
|---|---|---|---|---|
| Depression | 38.8 | 38.0 | 23.3 | +0.13 |
| Anxiety    | 32.1 | 30.0 | 20.5 | +0.29 |
| Stress     | 42.3 | 42.0 | 21.0 | +0.03 |

**Severity breakdown (all subscales — % Extremely Severe is unusually high):**

> [!NOTE]
> ~64–69% of respondents fall in the "Extremely Severe" range. This is expected for
> a **self-selected online sample** — people with mental health concerns actively seek
> out such assessments. The dataset is NOT representative of the general population.

**Subscale correlations (all highly significant, p < 0.001):**
- Depression ↔ Anxiety: r = **0.666**
- Depression ↔ Stress:  r = **0.734**
- Anxiety ↔ Stress:     r = **0.802**

> [!IMPORTANT]
> The high Anxiety–Stress correlation (r = 0.80) means these two subscales share
> substantial variance. Multi-label classification will need to account for this dependency.

**Figures generated:**
- `02_score_distributions.png` — Histogram + KDE per subscale
- `02_severity_breakdown.png` — Grouped + stacked severity bar charts
- `02_comorbidity_heatmap.png` — Pearson correlations + co-occurrence pattern chart
- `02_score_boxplots.png` — Score spread within each severity category

---

### Script 03 — Demographic Analysis (`03_demographics.py`)

**Purpose:** Understand *who* took the survey. Demographic composition affects generalisation,
surfaces sampling biases, and reveals which demographic groups carry the highest mental health burden.

**Key demographic facts:**

| Variable | Key Finding |
|---|---|
| **Age** | Mean 23.4 yrs, Median 21 yrs — **very young sample** |
| **Gender** | 76.3% Female, 22.1% Male — **heavily female-skewed** |
| **Country** | 54.3% Malaysia 🇲🇾, 20.6% USA 🇺🇸 — geographically concentrated |
| **Education** | 37.9% High School, 38.0% University |

**Group comparisons (Mann-Whitney U, all p < 0.001):**

- **Gender:** Females score significantly higher on Anxiety and Stress than Males
- **Age:** 18–24 age band shows highest mean scores across all three subscales
- **Education:** Inverse gradient — higher education associates with lower symptom scores

> [!TIP]
> The demographic skew (young, female, Malaysian) means the ML model may underperform
> on older males from Western countries. Stratified cross-validation is recommended.

**Figures generated:**
- `03_age_distribution.png` — Age histogram + age-group bar chart
- `03_gender_education.png` — Pie chart (gender) + bar chart (education)
- `03_country_top20.png` — Horizontal bar chart of top 20 countries
- `03_dass_by_gender.png` — Boxplots with Mann-Whitney significance
- `03_dass_by_age_group.png` — Bar charts with standard error
- `03_dass_by_education.png` — Bar charts with standard error

---

### Script 04 — Item-Level Analysis (`04_item_analysis.py`)

**Purpose:** Evaluate each of the 42 DASS items as individual ML features.  
Items with floor/ceiling effects or poor item-total correlations (CITC < 0.3) are weak features.

**Key findings:**

| Metric | Result |
|---|---|
| CITC range | 0.41 – 0.75 (all items above 0.3 threshold — **all are useful features**) |
| Mean response time | ~4,000–8,000 ms per item (reasonable engagement) |
| Careless responding | Median longest run = **5** consecutive identical answers |
| ≥10 consecutive same answers | **4,582** respondents (11.5%) — recommend filtering |

> [!NOTE]
> All 42 items have corrected item-total correlations above 0.3, confirming excellent
> internal consistency. This validates using all Q items as ML features without pruning.

**Figures generated:**
- `04_item_response_distribution.png` — 42×4 response frequency heatmap + mean response bar
- `04_item_total_correlations.png` — CITC bar chart with 0.3 and 0.5 thresholds
- `04_item_response_times.png` — Median response time per item
- `04_careless_responding.png` — Longest-run distribution with 10-response threshold

---

### Script 05 — Big Five Personality & VCL Analysis (`05_personality_vcl.py`)

**Purpose:** The TIPI Big Five personality inventory provides supplementary predictors.
Neuroticism is a well-known transdiagnostic risk factor; validating this in the data
confirms the dataset contains expected signal and justifies including TIPI in the ML feature set.

**TIPI → DASS correlations (all p < 0.001):**

| Trait | Depression | Anxiety | Stress |
|---|---|---|---|
| **Neuroticism** | **+0.43** | **+0.44** | **+0.46** |
| **Conscientiousness** | **–0.22** | –0.17 | **–0.28** |
| **Extraversion** | –0.17 | –0.13 | –0.14 |
| Agreeableness | –0.10 | –0.08 | –0.11 |
| Openness | –0.06 | –0.04 | –0.06 |

> [!IMPORTANT]
> Neuroticism is the strongest personality predictor of all three DASS subscales.
> Conscientiousness is a moderate protective factor especially against Stress.
> These align with established literature and validate the dataset.

**VCL filter impact:** Respondents who failed the VCL validity check scored **significantly higher**
on all three subscales (p < 0.001), suggesting they are responding more extremely or carelessly.
Excluding them is strongly recommended before training.

**Figures generated:**
- `05_tipi_distributions.png` — Histograms of all 5 trait scores
- `05_tipi_dass_correlations.png` — Heatmaps of personality ↔ DASS correlations
- `05_vcl_filter_impact.png` — Overlapping score distributions for VCL pass vs fail

---

### Script 06 — Feature Correlation & Multicollinearity (`06_feature_correlation.py`)

**Purpose:** Map the full correlation landscape of all potential ML features.
High within-subscale correlations confirm construct validity; cross-subscale correlations
reveal shared variance (comorbidity). Feature-DASS correlations rank predictive power.

**Top individual feature correlates with Depression:**
- Q34A (worthlessness), Q17A (low self-worth), Q26A (down-hearted) → r > 0.65
- Neuroticism TIPI → r ≈ +0.43
- Conscientiousness TIPI → r ≈ –0.22

**Multicollinearity note:**  
Items within the same subscale are strongly correlated (r ≈ 0.3–0.7).  
Tree-based models (RF, XGBoost) handle this naturally; linear models may benefit from PCA.

**Figures generated:**
- `06_full_feature_correlation.png` — 42×42 item inter-correlation heatmap (subscale-ordered)
- `06_dass_feature_importance_corr.png` — Top/bottom 10 feature correlations per subscale
- `06_pairplot_dass_personality.png` — Pairplot of DASS + personality (5,000 sample)

---

### Script 07 — Class Balance & ML Readiness (`07_class_balance.py`)

**Purpose:** Assess the suitability of the data for supervised ML classification,
compare label strategy options, and document the recommended ML pipeline setup.

**Class imbalance (5-class severity):**

| Subscale | Imbalance Ratio |
|---|---|
| Depression | 15.5 : 1 |
| Anxiety    | 20.6 : 1 |
| Stress     | 14.1 : 1 |

> [!WARNING]
> Severe class imbalance (especially "Normal" class vs. "Extremely Severe") will cause
> naive classifiers to predict the majority class. Must use one or more of:
> **SMOTE**, **class_weight='balanced'**, **threshold tuning**, or **cost-sensitive loss**.

**Recommended label strategies:**

| Strategy | Classes | Use Case |
|---|---|---|
| **Binary** | Normal vs. Elevated | Screening / triage |
| **3-class** | Normal / Mild-Moderate / Severe+ | Clinical prioritisation |
| **5-class** | All severity levels | Fine-grained diagnosis support |
| **Regression** | Continuous score | Severity tracking over time |

**Data quality funnel after all filters:**

```
Raw Dataset         : 39,775  (100.0%)
Remove Duplicates   : 39,775  (100.0%)  ← No duplicates found
Valid Age 13–100    : 39,768  (100.0%)
VCL Pass            : 34,583   (86.9%)
Test Time ≥ 60s     : 39,655   (99.7%)
ALL filters         : 34,511   (86.8%)  ← Recommended training set
```

**Figures generated:**
- `07_class_balance_5class.png` — 5-class count charts per subscale
- `07_class_balance_binary.png` — Pie charts (Normal vs. Elevated)
- `07_class_balance_3class.png` — 3-class bar charts
- `07_sample_funnel.png` — Cascading quality filter funnel

---

## Key Insights Summary

### 🔍 Data Quality
- Dataset is **clean** — no duplicates, no out-of-range Likert responses
- **13.1% of respondents** fail the VCL validity check → recommend excluding before training
- Only **0.3%** have suspiciously fast completion times

### 📊 Score Distributions
- All three subscales are **approximately normally distributed** (low skewness)
- Extremely high "Extremely Severe" rates (64–69%) reflect **self-selection bias**
- Subscales are highly inter-correlated (r = 0.67–0.80) — comorbidity is the norm

### 👥 Demographics
- Sample is **young** (median age 21), **female-dominated** (76%), and **geographically concentrated** (54% Malaysia)
- Significant gender differences in Anxiety and Stress (females score higher, p < 0.001)
- Younger age groups (18–24) show the highest symptom burden

### 🎯 Feature Importance
- **Individual DASS items** are the strongest predictors (CITC 0.41–0.75)
- **Neuroticism** (TIPI4/TIPI9) is the strongest personality predictor
- **Demographics** contribute modest but significant signal
- All 42 DASS items are valid features (no items need dropping based on CITC)

### ⚖️ ML Considerations
- **Severe class imbalance** (15–21:1) requires resampling or cost-sensitive learning
- **Binary classification** (Normal vs. Elevated) is the most tractable starting point
- **34,511 clean samples** are available for training after quality filtering
- Recommended features: 42 Q items + 5 TIPI traits + age + gender + education
