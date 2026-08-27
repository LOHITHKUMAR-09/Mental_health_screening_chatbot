"""
Phase 8 Review 1 - Full End-to-End Verification Test
Covers all checklist items:
  1. E2E: register -> login -> session -> 26-question screening -> results
  2. Scoring accuracy (PHQ-9, GAD-7, PSS-10) verified against known answers
  3. Crisis detection (English + Hinglish) with guardrail response
  4. ML model prediction (risk label, confidence, SHAP)
  5. API docs endpoint accessible (/docs, /openapi.json)
"""

import sys, time, json, requests

BASE = "http://localhost:8000"
API  = f"{BASE}/api/v1"
PASS = 0
FAIL = 0

def check(label, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}" + (f"  ({detail})" if detail else ""))

def section(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

# ── 1. Health & API Docs ─────────────────────────────────────────
section("1. HEALTH & API DOCS")
r = requests.get(f"{BASE}/health", timeout=5)
check("Health endpoint 200", r.status_code == 200)
check("Database connected", r.json().get("database") == "connected")
r2 = requests.get(f"{BASE}/docs", timeout=5)
check("FastAPI /docs page accessible", r2.status_code == 200)
r3 = requests.get(f"{BASE}/openapi.json", timeout=5)
check("OpenAPI JSON accessible", r3.status_code == 200)
if r3.status_code == 200:
    paths = r3.json().get("paths", {})
    check("Chat endpoint in OpenAPI spec", any("chat" in p for p in paths))
    check("ML endpoint in OpenAPI spec",   any("/ml/" in p for p in paths))
    check("Results endpoint in OpenAPI spec", any("results" in p for p in paths))

# ── 2. Full E2E Screening Flow ───────────────────────────────────
section("2. FULL E2E: REGISTER -> LOGIN -> SCREEN -> RESULTS")
ts = int(time.time())
email, pwd = f"review1_{ts}@university.edu", "ReviewPass999!"

r = requests.post(f"{API}/auth/register", json={"email": email, "password": pwd, "role": "student"}, timeout=10)
check("User registration (201)", r.status_code == 201, r.text[:60])

r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=10)
check("User login + JWT (200)", r.status_code == 200, r.text[:60])
token = r.json().get("access_token") if r.status_code == 200 else ""
hdrs  = {"Authorization": f"Bearer {token}"}

r = requests.post(f"{API}/sessions/start", headers=hdrs, timeout=10)
check("New session created (201)", r.status_code == 201, r.text[:60])
sid = r.json().get("session_id") if r.status_code == 201 else None

def chat(msg):
    return requests.post(f"{API}/chat/message",
                         json={"session_id": sid, "message": msg},
                         headers=hdrs, timeout=15)

if sid:
    # Greeting / Consent / Background
    for msg in ["Hello MindEase", "I consent to participate", "I am a 3rd year CS student"]:
        r = chat(msg)
        check(f"Chat message accepted: '{msg[:20]}...'", r.status_code == 200, r.text[:60])

    # PHQ-9: known responses -> total = 9 (1+1+1+1+1+1+1+1+1=9, mild)
    PHQ9 = [1,1,1,1,1,1,1,1,1]
    for i,v in enumerate(PHQ9):
        r = chat(str(v))
        check(f"PHQ-9 item {i+1}", r.status_code == 200)

    # GAD-7: total = 14 (2*7, moderate)
    GAD7 = [2,2,2,2,2,2,2]
    for i,v in enumerate(GAD7):
        r = chat(str(v))
        check(f"GAD-7 item {i+1}", r.status_code == 200)

    # PSS-10: realistic moderate stress responses
    PSS10 = [3,2,3,1,1,3,2,2,2,3]
    for i,v in enumerate(PSS10):
        r = chat(str(v))
        check(f"PSS-10 item {i+1}", r.status_code == 200)

    last = r.json()
    check("Screening marked complete", last.get("screening_complete") == True,
          f"state={last.get('current_state')}")

    # ── 3. Scoring Accuracy ───────────────────────────────────────
    section("3. SCORING ACCURACY VERIFICATION")
    r = requests.get(f"{API}/sessions/{sid}/results", headers=hdrs, timeout=10)
    check("Results endpoint 200", r.status_code == 200, r.text[:80])
    if r.status_code == 200:
        res = r.json()
        phq9_score  = res.get("phq9_score")
        gad7_score  = res.get("gad7_score")
        pss10_score = res.get("pss10_score")
        phq9_sev    = res.get("phq9_severity")
        gad7_sev    = res.get("gad7_severity")
        comp_risk   = res.get("composite_risk_level") or res.get("risk_level")
        ml_label    = res.get("ml_risk_label")
        ml_conf     = res.get("ml_confidence")
        shap        = res.get("shap_top_features", {})
        coping      = res.get("coping_suggestions", [])

        print(f"""
     PHQ-9  : {phq9_score}  (expected 9)  severity={phq9_sev}
     GAD-7  : {gad7_score}  (expected 14) severity={gad7_sev}
     PSS-10 : {pss10_score}
     Composite Risk : {comp_risk}
     ML Label       : {ml_label}  Confidence: {(ml_conf or 0)*100:.1f}%
     SHAP features  : {list(shap.keys())[:3]}
     Coping tips    : {len(coping)} items
        """)
        check("PHQ-9 score = 9", phq9_score == 9, f"got {phq9_score}")
        check("PHQ-9 severity = mild", phq9_sev == "mild", f"got {phq9_sev}")
        check("GAD-7 score = 14", gad7_score == 14, f"got {gad7_score}")
        check("GAD-7 severity = moderate", gad7_sev == "moderate", f"got {gad7_sev}")
        check("PSS-10 score computed (not None)", pss10_score is not None)
        check("Composite risk level present", comp_risk in ("low","moderate","high"), f"got {comp_risk}")
        check("ML risk label returned", ml_label is not None)
        check("ML confidence returned", ml_conf is not None)
        check("SHAP top features returned", bool(shap))
        check("Coping suggestions present", len(coping) > 0)
        check("Crisis resources included", bool(res.get("crisis_resources")))

# ── 4. Crisis Detection ───────────────────────────────────────────
section("4. CRISIS DETECTION GUARDRAIL")
r_anon = requests.post(f"{API}/auth/anonymous", timeout=10)
anon_token = r_anon.json().get("access_token")
ah = {"Authorization": f"Bearer {anon_token}"}
r_sess = requests.post(f"{API}/sessions/start", headers=ah, timeout=10)
csid = r_sess.json().get("session_id")

for msg in ["hi", "yes i agree", "first year student"]:
    requests.post(f"{API}/chat/message", json={"session_id": csid, "message": msg}, headers=ah, timeout=10)

# English crisis
r = requests.post(f"{API}/chat/message", json={"session_id": csid, "message": "I want to kill myself"}, headers=ah, timeout=10)
check("Crisis message returns 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    check("is_crisis = True (English)", d.get("is_crisis") == True, str(d.get("is_crisis")))
    bot = d.get("bot_message","")
    check("Helpline in response", any(h in bot for h in ["9152987821","1860","Vandrevala","iCall"]), bot[:100])

# Hinglish crisis
r = requests.post(f"{API}/chat/message", json={"session_id": csid, "message": "main mar jana chahta hun"}, headers=ah, timeout=10)
check("Hinglish crisis returns 200", r.status_code == 200)
if r.status_code == 200:
    check("is_crisis = True (Hinglish)", r.json().get("is_crisis") == True)

# Safe idiom — must NOT trigger
r = requests.post(f"{API}/chat/message", json={"session_id": csid, "message": "this exam is killing me"}, headers=ah, timeout=10)
if r.status_code == 200:
    check("Safe idiom NOT flagged as crisis", r.json().get("is_crisis") != True)

# ── 5. Direct ML Predict Endpoint ────────────────────────────────
section("5. DIRECT ML PREDICT ENDPOINT")
ml_body = {
    "phq9_responses":  {str(i): 2 for i in range(1,10)},
    "gad7_responses":  {str(i): 2 for i in range(1,8)},
    "pss10_responses": {str(i): 3 for i in range(1,11)},
}
r = requests.post(f"{API}/ml/predict", json=ml_body, headers=hdrs, timeout=10)
check("ML /predict returns 200", r.status_code == 200, r.text[:80])
if r.status_code == 200:
    ml = r.json()
    check("risk_label in response", "risk_label" in ml)
    check("confidence in response",  "confidence" in ml)
    has_shap = "shap_features" in ml or "shap_top_features" in ml
    check("shap_features in response", has_shap)
    print(f"     Direct ML: {ml.get('risk_label')} @ {(ml.get('confidence') or 0)*100:.1f}%")

# ── Summary ───────────────────────────────────────────────────────
section("PHASE 8 REVIEW 1 — FINAL SUMMARY")
total = PASS + FAIL
print(f"\n  PASSED : {PASS} / {total}")
print(f"  FAILED : {FAIL} / {total}")
if FAIL == 0:
    print("\n  *** ALL CHECKS PASSED — REVIEW 1 READY TO PRESENT ***")
    sys.exit(0)
else:
    print(f"\n  {FAIL} item(s) need attention before Review 1.")
    sys.exit(1)
