import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")
from app.ml.predictor import ml_predictor

sample = {
    "phq9":  {1:2, 2:3, 3:2, 4:2, 5:1, 6:2, 7:1, 8:1, 9:0},
    "gad7":  {1:3, 2:2, 3:3, 4:2, 5:1, 6:2, 7:2},
    "pss10": {1:3, 2:3, 3:2, 4:1, 5:1, 6:3, 7:1, 8:1, 9:2, 10:3},
}
label, conf, shap = ml_predictor.predict(sample)
print(f"Risk Label : {label}")
print(f"Confidence : {conf*100:.1f}%")
print(f"Top SHAP   : {list(shap.keys())[:3]}")
print("ML PREDICTOR TEST PASSED")
