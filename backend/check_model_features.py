import joblib
model = joblib.load(r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\ml\models\best_model.pkl")
scaler = model.named_steps["scaler"]
print(f"Feature count: {scaler.n_features_in_}")
print(f"Feature names: {list(scaler.feature_names_in_)}")
