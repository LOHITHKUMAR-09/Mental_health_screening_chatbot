"""
run_all_eda.py
==============
Master runner — executes all EDA scripts in sequence.

REASON: A single entry-point ensures reproducibility. Anyone who clones this
repo can reproduce the entire EDA by running one command:
    python EDA/scripts/run_all_eda.py

All outputs (figures + reports) are written to EDA/outputs/.
"""

import subprocess, sys, os, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)   # EDA/  parent = ML_Mental_Health_Screening/

# Prefer the project venv Python (has all required packages installed)
VENV_PYTHON = os.path.join(PROJECT_ROOT, "ml", ".venv", "Scripts", "python.exe")
PYTHON = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

SCRIPTS = [
    "01_data_quality.py",
    "02_dass_scores.py",
    "03_demographics.py",
    "04_item_analysis.py",
    "05_personality_vcl.py",
    "06_feature_correlation.py",
    "07_class_balance.py",
]

print("=" * 65)
print("  DASS EDA Master Runner")
print("=" * 65)
total_start = time.time()

for script in SCRIPTS:
    path = os.path.join(SCRIPT_DIR, script)
    print(f"\n{'-'*65}")
    print(f"  Running: {script}")
    print(f"{'-'*65}")
    start = time.time()
    result = subprocess.run([PYTHON, path], capture_output=False)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\n  FAILED: {script}  (exit code {result.returncode})")
        sys.exit(result.returncode)
    print(f"  Done in {elapsed:.1f}s")

total_elapsed = time.time() - total_start
print(f"\n{'=' * 65}")
print(f"  All EDA scripts completed in {total_elapsed:.0f}s")
print(f"  Figures  -> EDA/outputs/figures/")
print(f"  Reports  -> EDA/outputs/reports/")
print(f"{'=' * 65}\n")
