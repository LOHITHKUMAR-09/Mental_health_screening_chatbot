"""
Synthetic dataset generator for ML mental health screening model.
Generates realistic PHQ-9 / GAD-7 / PSS-10 response data
based on published clinical distributions.
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)


def generate_synthetic_dataset(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic questionnaire responses with realistic distributions.
    
    Risk level distribution (approximate real-world prevalence in university students):
      - Low risk:      ~50% of students
      - Moderate risk: ~35% of students
      - High risk:     ~15% of students
    """
    records = []

    # Risk level proportions
    risk_proportions = {"low": 0.50, "moderate": 0.35, "high": 0.15}

    for risk_label, proportion in risk_proportions.items():
        n = int(n_samples * proportion)

        if risk_label == "low":
            # Low risk: minimal/mild scores
            phq9_means  = [0.3] * 9   # avg item score ~0.3 (mostly "not at all")
            gad7_means  = [0.3] * 7
            pss10_means = [1.0] * 10
        elif risk_label == "moderate":
            # Moderate risk: mild to moderate scores
            phq9_means  = [1.2] * 9
            gad7_means  = [1.1] * 7
            pss10_means = [2.0] * 10
        else:
            # High risk: moderate to severe scores
            phq9_means  = [2.1] * 9
            gad7_means  = [2.0] * 7
            pss10_means = [2.9] * 10

        for _ in range(n):
            row = {"risk_label": risk_label}

            # PHQ-9: 9 items, 0-3 scale
            for i in range(1, 10):
                val = int(np.clip(np.round(np.random.normal(phq9_means[i-1], 0.8)), 0, 3))
                row[f"phq9_item_{i}"] = val

            # GAD-7: 7 items, 0-3 scale
            for i in range(1, 8):
                val = int(np.clip(np.round(np.random.normal(gad7_means[i-1], 0.8)), 0, 3))
                row[f"gad7_item_{i}"] = val

            # PSS-10: 10 items, 0-4 scale
            for i in range(1, 11):
                val = int(np.clip(np.round(np.random.normal(pss10_means[i-1], 1.0)), 0, 4))
                row[f"pss10_item_{i}"] = val

            records.append(row)

    df = pd.DataFrame(records).sample(frac=1, random_state=42).reset_index(drop=True)

    # Compute subscale totals
    df["phq9_total"] = df[[f"phq9_item_{i}" for i in range(1, 10)]].sum(axis=1)
    df["gad7_total"] = df[[f"gad7_item_{i}" for i in range(1, 8)]].sum(axis=1)

    # PSS-10 with reverse scoring
    pss_cols_normal  = [f"pss10_item_{i}" for i in [1, 2, 3, 6, 9, 10]]
    pss_cols_reverse = [f"pss10_item_{i}" for i in [4, 5, 7, 8]]
    df["pss10_total"] = (
        df[pss_cols_normal].sum(axis=1) +
        df[pss_cols_reverse].apply(lambda col: 4 - col).sum(axis=1)
    )

    # Derived features
    df["phq9_max_item"]      = df[[f"phq9_item_{i}" for i in range(1, 10)]].max(axis=1)
    df["gad7_max_item"]      = df[[f"gad7_item_{i}" for i in range(1, 8)]].max(axis=1)
    df["phq9_severe_items"]  = df[[f"phq9_item_{i}" for i in range(1, 10)]].ge(2).sum(axis=1)
    df["gad7_severe_items"]  = df[[f"gad7_item_{i}" for i in range(1, 8)]].ge(2).sum(axis=1)
    df["phq9_variance"]      = df[[f"phq9_item_{i}" for i in range(1, 10)]].var(axis=1)
    df["gad7_variance"]      = df[[f"gad7_item_{i}" for i in range(1, 8)]].var(axis=1)
    df["phq9_item9_suicidal"]= df["phq9_item_9"]
    df["time_of_day_bin"]    = np.random.randint(0, 4, size=len(df))
    df["is_returning_user"]  = np.random.randint(0, 2, size=len(df))
    df["session_number"]     = np.random.randint(1, 4, size=len(df))

    return df


if __name__ == "__main__":
    print("Generating synthetic dataset...")
    df = generate_synthetic_dataset(n_samples=1000)
    out_path = Path(__file__).parent.parent / "data" / "synthetic" / "synthetic_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"Dataset generated: {len(df)} samples")
    print(f"Risk distribution:\n{df['risk_label'].value_counts()}")
    print(f"Saved to: {out_path}")
