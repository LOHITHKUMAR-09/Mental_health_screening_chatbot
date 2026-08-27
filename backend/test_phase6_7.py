import httpx
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE_URL = "http://localhost:8000/api/v1"

def test_ml_and_frontend_pipeline():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    print("=" * 60)
    print("PHASE 6 (ML PIPELINE) & PHASE 7 (FRONTEND) INTEGRATION TEST")
    print("=" * 60)

    # 1. Direct ML Predict Endpoint
    print("\n[1] Testing POST /api/v1/ml/predict ...")
    ml_payload = {
        "phq9_responses": {1: 2, 2: 3, 3: 2, 4: 2, 5: 1, 6: 2, 7: 1, 8: 1, 9: 0},
        "gad7_responses": {1: 3, 2: 2, 3: 3, 4: 2, 5: 1, 6: 2, 7: 2},
        "pss10_responses": {1: 3, 2: 3, 3: 2, 4: 1, 5: 1, 6: 3, 7: 1, 8: 1, 9: 2, 10: 3},
    }
    res = client.post("/ml/predict", json=ml_payload)
    assert res.status_code == 200, f"ML predict failed: {res.text}"
    ml_data = res.json()
    print(f"  - Model: {ml_data['model_name']}")
    print(f"  - Predicted Risk: {ml_data['risk_label'].upper()}")
    print(f"  - Confidence: {ml_data['confidence'] * 100:.1f}%")
    print(f"  - Top SHAP Features: {list(ml_data['top_feature_importance'].keys())[:3]}")
    print("[PASS] 1. ML Direct Inference & Explainability Endpoint")

    # 2. End-to-end Session with ML Results
    print("\n[2] Testing Full Screening Session -> ML Results Generation ...")
    sess = client.post("/sessions/start").json()
    sid = sess["session_id"]

    # Submit sample questionnaire items
    for item in range(1, 10):
        client.post("/screening/submit-item", json={"session_id": sid, "instrument": "phq9", "item_number": item, "response_value": 2})
    for item in range(1, 8):
        client.post("/screening/submit-item", json={"session_id": sid, "instrument": "gad7", "item_number": item, "response_value": 2})
    for item in range(1, 11):
        client.post("/screening/submit-item", json={"session_id": sid, "instrument": "pss10", "item_number": item, "response_value": 3})

    # Fetch Results
    res = client.get(f"/results/{sid}")
    assert res.status_code == 200, f"Results failed: {res.text}"
    results = res.json()
    print(f"  - PHQ-9: {results['phq9_score']}/27 ({results['phq9_severity']})")
    print(f"  - GAD-7: {results['gad7_score']}/21 ({results['gad7_severity']})")
    print(f"  - PSS-10: {results['pss10_score']}/40 ({results['pss10_severity']})")
    print(f"  - Rule-based Risk: {results['rule_based_risk']}")
    print(f"  - ML Model Risk Label: {results['ml_risk_label']}")
    print(f"  - ML Confidence: {results['ml_confidence'] * 100:.1f}%")
    print(f"  - Coping Suggestions: {len(results['coping_suggestions'])} tips generated")
    assert results["ml_risk_label"] is not None
    print("[PASS] 2. Results Endpoint with Clinical Scoring & ML Risk Model")

    # 3. Crisis Detection in Hinglish
    print("\n[3] Testing Multilingual Crisis Detection (Hinglish) ...")
    crisis_res = client.post("/chat/message", json={"session_id": sid, "message": "Mujhe jeene ka mann nahi hai, main mar jana chahta hu"}).json()
    assert crisis_res["is_crisis"] is True
    assert "9152987821" in crisis_res["bot_message"]
    print("  - Triggered safety response with emergency helplines")
    print("[PASS] 3. Multilingual Crisis Safety Guardrail")

    print("\n" + "=" * 60)
    print("ALL PHASE 5, 6, AND 7 END-TO-END TESTS PASSED!")
    print("=" * 60)

test_ml_and_frontend_pipeline()
