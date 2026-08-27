# Mental Health Screening Instruments Reference

> **Clinical Note**: These instruments are validated screening tools, not diagnostic tools.
> MindEase uses them for psychoeducation and to identify individuals who may benefit from professional support.
> Results should always be interpreted by a qualified mental health professional.

---

## 1. PHQ-9 — Patient Health Questionnaire-9

### Overview

| Property | Value |
|----------|-------|
| **Full Name** | Patient Health Questionnaire-9 |
| **Purpose** | Screen for Major Depressive Disorder (MDD) |
| **Developer** | Kroenke, Spitzer & Williams (2001) |
| **Time Frame** | Past 2 weeks |
| **Items** | 9 |
| **Scale per Item** | 0–3 |
| **Total Score Range** | 0–27 |
| **Sensitivity** | 88% (for MDD at cutoff ≥ 10) |
| **Specificity** | 88% (for MDD at cutoff ≥ 10) |
| **License** | Public domain (Pfizer Inc.) |

### All 9 Items

> *"Over the last 2 weeks, how often have you been bothered by any of the following problems?"*

| Item | # | Question Text | Clinical Domain |
|------|---|--------------|-----------------|
| PHQ-1 | 1 | Little interest or pleasure in doing things | Anhedonia |
| PHQ-2 | 2 | Feeling down, depressed, or hopeless | Depressed mood |
| PHQ-3 | 3 | Trouble falling or staying asleep, or sleeping too much | Sleep disturbance |
| PHQ-4 | 4 | Feeling tired or having little energy | Fatigue |
| PHQ-5 | 5 | Poor appetite or overeating | Appetite changes |
| PHQ-6 | 6 | Feeling bad about yourself — or that you are a failure or have let yourself or your family down | Worthlessness / guilt |
| PHQ-7 | 7 | Trouble concentrating on things, such as reading the newspaper or watching television | Concentration difficulty |
| PHQ-8 | 8 | Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual | Psychomotor changes |
| PHQ-9 | 9 | Thoughts that you would be better off dead, or of hurting yourself in some way | **Suicidal ideation ⚠️** |

### Response Scale

| Value | Label |
|-------|-------|
| 0 | Not at all |
| 1 | Several days |
| 2 | More than half the days |
| 3 | Nearly every day |

### Scoring

```
PHQ-9 Total Score = Sum of all 9 item scores (0–27)
```

### Severity Cutoffs

| Score Range | Severity Level | Recommended Action |
|-------------|---------------|-------------------|
| **0 – 4** | 🟢 Minimal / None | Watchful waiting; repeat at next visit |
| **5 – 9** | 🟡 Mild | Use clinical judgment; consider counseling, follow up |
| **10 – 14** | 🟠 Moderate | Treatment plan, counseling and/or pharmacotherapy |
| **15 – 19** | 🔴 Moderately Severe | Active treatment with pharmacotherapy and/or psychotherapy |
| **20 – 27** | 🔴 Severe | Immediate initiation of pharmacotherapy; if not, urgent referral |

### Crisis Item Logic (Item 9)

```
IF PHQ9_Q9 >= 1:
    → Trigger CRISIS_PROTOCOL state
    → Display crisis resources immediately
    → Create CrisisAlert database record
    → Notify clinical staff (if configured)

Item 9 score interpretation:
    1 = "Several days" → Assess further, provide resources
    2 = "More than half the days" → High concern, strong intervention
    3 = "Nearly every day" → Emergency referral recommended
```

### Scoring Formula (Python)

```python
def compute_phq9(answers: list[int]) -> dict:
    """
    args:
        answers: list of 9 integers, each 0-3
    returns:
        dict with score, severity, crisis_flag
    """
    assert len(answers) == 9, "PHQ-9 requires exactly 9 answers"
    assert all(0 <= a <= 3 for a in answers), "Each answer must be 0-3"

    total = sum(answers)
    crisis_flag = answers[8] >= 1  # Item 9 (index 8)

    if total <= 4:
        severity = "minimal"
    elif total <= 9:
        severity = "mild"
    elif total <= 14:
        severity = "moderate"
    elif total <= 19:
        severity = "moderately_severe"
    else:
        severity = "severe"

    return {
        "score": total,
        "severity": severity,
        "crisis_flag": crisis_flag,
        "item_scores": answers,
        "max_score": 27,
        "instrument": "PHQ-9"
    }
```

### Key References

- Kroenke K, Spitzer RL, Williams JB. **The PHQ-9: validity of a brief depression severity measure.** *J Gen Intern Med.* 2001;16(9):606-613.
- Spitzer RL, et al. **Validation and utility of a self-report version of PRIME-MD.** *JAMA.* 1999;282(18):1737-1744.

---

## 2. GAD-7 — Generalized Anxiety Disorder-7

### Overview

| Property | Value |
|----------|-------|
| **Full Name** | Generalized Anxiety Disorder-7 |
| **Purpose** | Screen for Generalized Anxiety Disorder (GAD) |
| **Developer** | Spitzer, Kroenke, Williams & Löwe (2006) |
| **Time Frame** | Past 2 weeks |
| **Items** | 7 |
| **Scale per Item** | 0–3 |
| **Total Score Range** | 0–21 |
| **Sensitivity** | 89% (for GAD at cutoff ≥ 10) |
| **Specificity** | 82% (for GAD at cutoff ≥ 10) |
| **License** | Public domain (Pfizer Inc.) |

### All 7 Items

> *"Over the last 2 weeks, how often have you been bothered by the following problems?"*

| Item | # | Question Text | Clinical Domain |
|------|---|--------------|-----------------|
| GAD-1 | 1 | Feeling nervous, anxious, or on edge | Core anxiety |
| GAD-2 | 2 | Not being able to stop or control worrying | Worry control |
| GAD-3 | 3 | Worrying too much about different things | Excessive worry |
| GAD-4 | 4 | Trouble relaxing | Relaxation difficulty |
| GAD-5 | 5 | Being so restless that it's hard to sit still | Motor restlessness |
| GAD-6 | 6 | Becoming easily annoyed or irritable | Irritability |
| GAD-7 | 7 | Feeling afraid as if something awful might happen | Anticipatory anxiety |

### Response Scale

| Value | Label |
|-------|-------|
| 0 | Not at all |
| 1 | Several days |
| 2 | More than half the days |
| 3 | Nearly every day |

### Scoring

```
GAD-7 Total Score = Sum of all 7 item scores (0–21)
```

### Severity Cutoffs

| Score Range | Severity Level | Recommended Action |
|-------------|---------------|-------------------|
| **0 – 4** | 🟢 Minimal | Normal; reassure |
| **5 – 9** | 🟡 Mild | Monitor; possible watchful waiting |
| **10 – 14** | 🟠 Moderate | Consider therapy (CBT); possible medication |
| **15 – 21** | 🔴 Severe | Active treatment; referral to specialist |

### Scoring Formula (Python)

```python
def compute_gad7(answers: list[int]) -> dict:
    """
    args:
        answers: list of 7 integers, each 0-3
    returns:
        dict with score and severity
    """
    assert len(answers) == 7, "GAD-7 requires exactly 7 answers"
    assert all(0 <= a <= 3 for a in answers), "Each answer must be 0-3"

    total = sum(answers)

    if total <= 4:
        severity = "minimal"
    elif total <= 9:
        severity = "mild"
    elif total <= 14:
        severity = "moderate"
    else:
        severity = "severe"

    return {
        "score": total,
        "severity": severity,
        "item_scores": answers,
        "max_score": 21,
        "instrument": "GAD-7"
    }
```

### Key Reference

- Spitzer RL, Kroenke K, Williams JBW, Löwe B. **A brief measure for assessing generalized anxiety disorder.** *Arch Intern Med.* 2006;166(10):1092-1097.

---

## 3. PSS-10 — Perceived Stress Scale-10

### Overview

| Property | Value |
|----------|-------|
| **Full Name** | Perceived Stress Scale (10-item version) |
| **Purpose** | Measure subjective perception of stress |
| **Developer** | Sheldon Cohen, Tom Kamarck & Robin Mermelstein (1983) |
| **Time Frame** | Past 1 month |
| **Items** | 10 (including 4 reverse-scored items) |
| **Scale per Item** | 0–4 |
| **Total Score Range** | 0–40 |
| **License** | Free for non-commercial use (Sheldon Cohen, CMU) |

### All 10 Items

> *"In the last month, how often have you..."*

| Item | # | Question Text | Scoring Type |
|------|---|--------------|--------------|
| PSS-1 | 1 | Been upset because of something that happened unexpectedly? | Normal |
| PSS-2 | 2 | Felt that you were unable to control the important things in your life? | Normal |
| PSS-3 | 3 | Felt nervous and stressed? | Normal |
| PSS-4 | 4 | Felt confident about your ability to handle your personal problems? | **Reversed ↔️** |
| PSS-5 | 5 | Felt that things were going your way? | **Reversed ↔️** |
| PSS-6 | 6 | Found that you could not cope with all the things you had to do? | Normal |
| PSS-7 | 7 | Been able to control irritations in your life? | **Reversed ↔️** |
| PSS-8 | 8 | Felt that you were on top of things? | **Reversed ↔️** |
| PSS-9 | 9 | Been angered because of things that were outside of your control? | Normal |
| PSS-10 | 10 | Felt difficulties were piling up so high that you could not overcome them? | Normal |

> **Reverse-scored items**: 4, 5, 7, 8

### Response Scale

| Value | Label |
|-------|-------|
| 0 | Never |
| 1 | Almost never |
| 2 | Sometimes |
| 3 | Fairly often |
| 4 | Very often |

### Scoring

```
For normal items (1, 2, 3, 6, 9, 10):
    item_score = raw_value

For reversed items (4, 5, 7, 8):
    item_score = 4 - raw_value

PSS-10 Total Score = Sum of all 10 adjusted item scores (0–40)
```

### Severity Cutoffs

| Score Range | Stress Level | Interpretation |
|-------------|-------------|----------------|
| **0 – 13** | 🟢 Low Stress | Normal coping; stress is manageable |
| **14 – 26** | 🟡 Moderate Stress | Some stress-related challenges; consider stress management |
| **27 – 40** | 🔴 High Stress | Significant stress; recommend stress management programs / professional support |

> **Note**: PSS norms vary by population. Normative mean for general adults ≈ 13-15 (Cohen & Williamson, 1988).

### Reverse Score Lookup Table

| Raw Score | Reversed Score |
|-----------|---------------|
| 0 | 4 |
| 1 | 3 |
| 2 | 2 |
| 3 | 1 |
| 4 | 0 |

### Scoring Formula (Python)

```python
REVERSE_ITEMS = {3, 4, 6, 7}  # 0-indexed: PSS items 4,5,7,8

def compute_pss10(answers: list[int]) -> dict:
    """
    args:
        answers: list of 10 integers, each 0-4 (raw values)
    returns:
        dict with score, severity, and adjusted item scores
    """
    assert len(answers) == 10, "PSS-10 requires exactly 10 answers"
    assert all(0 <= a <= 4 for a in answers), "Each answer must be 0-4"

    adjusted = []
    for i, raw in enumerate(answers):
        if i in REVERSE_ITEMS:
            adjusted.append(4 - raw)
        else:
            adjusted.append(raw)

    total = sum(adjusted)

    if total <= 13:
        severity = "low"
    elif total <= 26:
        severity = "moderate"
    else:
        severity = "high"

    return {
        "score": total,
        "severity": severity,
        "raw_item_scores": answers,
        "adjusted_item_scores": adjusted,
        "reverse_items": [4, 5, 7, 8],  # 1-indexed for display
        "max_score": 40,
        "instrument": "PSS-10"
    }
```

### Key References

- Cohen S, Kamarck T, Mermelstein R. **A global measure of perceived stress.** *Journal of Health and Social Behavior.* 1983;24(4):385-396.
- Cohen S, Williamson G. **Perceived stress in a probability sample of the United States.** In: Spacapan S, Oskamp S (Eds.). *The Social Psychology of Health.* 1988:31-67.

---

## 4. Composite Scoring & ML Feature Engineering

### Combined Score Interpretation

The MindEase ML model uses all three instrument scores plus demographic features to predict an overall risk level.

```python
def compute_overall_risk(phq9_result: dict, gad7_result: dict, pss10_result: dict) -> str:
    """
    Compute overall risk level from all three instruments.
    This is a heuristic used as a feature engineering baseline
    before the Random Forest model makes its final prediction.
    """
    phq9_score = phq9_result["score"]
    gad7_score = gad7_result["score"]
    pss10_score = pss10_result["score"]

    # Normalize scores to 0-1 range
    phq9_norm = phq9_score / 27
    gad7_norm = gad7_score / 21
    pss10_norm = pss10_score / 40

    # Weighted composite (depression weighted slightly higher)
    composite = (phq9_norm * 0.40) + (gad7_norm * 0.35) + (pss10_norm * 0.25)

    if composite < 0.20:
        return "low"
    elif composite < 0.45:
        return "moderate"
    elif composite < 0.70:
        return "high"
    else:
        return "very_high"
```

### ML Feature Vector (Random Forest Input)

```python
features = [
    # Raw scores
    phq9_score,           # 0–27
    gad7_score,           # 0–21
    pss10_score,          # 0–40

    # Normalized scores
    phq9_score / 27,
    gad7_score / 21,
    pss10_score / 40,

    # Severity encodings (ordinal)
    phq9_severity_encoded,  # 0=minimal, 1=mild, 2=moderate, 3=mod-severe, 4=severe
    gad7_severity_encoded,  # 0=minimal, 1=mild, 2=moderate, 3=severe
    pss10_severity_encoded, # 0=low, 1=moderate, 2=high

    # Crisis flag
    phq9_crisis_flag,       # 0 or 1

    # Demographics
    age,
    gender_encoded,         # one-hot or label encoded
]
```

---

## 5. Recommendations Framework

### PHQ-9 Based Recommendations

| Severity | Recommendation Category | Example Resources |
|----------|------------------------|-------------------|
| Minimal | Wellness maintenance | Mindfulness apps, exercise |
| Mild | Self-help + monitoring | CBT workbooks, journaling |
| Moderate | Professional consultation | Therapist referral, GP visit |
| Mod-Severe | Active treatment | Psychiatry, medication eval |
| Severe | Urgent care | Emergency services, crisis lines |

### GAD-7 Based Recommendations

| Severity | Recommendation Category | Example Resources |
|----------|------------------------|-------------------|
| Minimal | Relaxation practices | Breathing exercises, yoga |
| Mild | Worry management | CBT techniques, journaling |
| Moderate | Therapy | CBT specialist, MBSR |
| Severe | Clinical treatment | Psychiatry, medication |

### PSS-10 Based Recommendations

| Level | Recommendation Category | Example Resources |
|-------|------------------------|-------------------|
| Low | Stress awareness | Continued healthy habits |
| Moderate | Stress management | Time management, mindfulness |
| High | Intensive support | Therapy, stress clinics, medical eval |
