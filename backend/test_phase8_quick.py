"""Phase 8 Quick Smoke Test - uses existing test_phase2_endpoints.py for full flow,
   then separately checks Phase 6/7/8 specific items."""
import sys, time, requests
BASE = "http://localhost:8000"
API  = f"{BASE}/api/v1"
PASS = 0; FAIL = 0

def check(label, ok, detail=""):
    global PASS, FAIL
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  -> {detail}" if detail else ""))
    if ok: PASS += 1
    else:  FAIL += 1

def section(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

# 1. API Docs
section("1. API DOCS")
check("Health 200",       requests.get(f"{BASE}/health").status_code == 200)
check("FastAPI /docs",    requests.get(f"{BASE}/docs").status_code == 200)
check("OpenAPI JSON",     requests.get(f"{BASE}/openapi.json").status_code == 200)
paths = requests.get(f"{BASE}/openapi.json").json().get("paths", {})
check("Chat in spec",     any("chat" in p for p in paths))
check("ML in spec",       any("/ml/" in p for p in paths))
check("Results in spec",  any("results" in p for p in paths))

# 2. Quick auth + session
section("2. AUTH & SESSION")
ts = int(time.time())
email, pwd = f"q8_{ts}@uni.edu", "Pass1234!"
r = requests.post(f"{API}/auth/register", json={"email": email, "password": pwd, "role": "student"})
check("Register", r.status_code == 201)
r = requests.post(f"{API}/auth/login", json={"email": email, "password": pwd})
check("Login + JWT", r.status_code == 200)
token = r.json().get("access_token", "")
H = {"Authorization": f"Bearer {token}"}
r = requests.post(f"{API}/sessions/start", headers=H)
check("Session created", r.status_code == 201)

# 3. Crisis detection (fast - no LLM)
section("3. CRISIS DETECTION")
r_anon = requests.post(f"{API}/auth/anonymous")
ah = {"Authorization": f"Bearer {r_anon.json().get('access_token')}"}
r_cs = requests.post(f"{API}/sessions/start", headers=ah)
csid = r_cs.json().get("session_id")
# Advance to background via scripted (no LLM needed for these transitions)
for msg in ["hi", "yes i agree", "2nd year"]:
    requests.post(f"{API}/chat/message", json={"session_id": csid, "message": msg}, headers=ah, timeout=10)

r = requests.post(f"{API}/chat/message",
    json={"session_id": csid, "message": "I want to kill myself"}, headers=ah, timeout=10)
check("Crisis returns 200",    r.status_code == 200)
d = r.json()
check("is_crisis = True",      d.get("is_crisis") == True, str(d.get("is_crisis")))
check("Helpline in response",  any(h in d.get("bot_message","") for h in ["9152987821","Vandrevala","iCall"]))

# Hinglish
r = requests.post(f"{API}/chat/message",
    json={"session_id": csid, "message": "main mar jana chahta hun"}, headers=ah, timeout=10)
check("Hinglish crisis detected", r.status_code == 200 and r.json().get("is_crisis") == True)

# Safe idiom
r = requests.post(f"{API}/chat/message",
    json={"session_id": csid, "message": "exam is killing me"}, headers=ah, timeout=10)
check("Safe idiom not flagged", r.status_code == 200 and r.json().get("is_crisis") != True)

# 4. Direct ML predict
section("4. ML INFERENCE")
ml_body = {
    "phq9_responses":  {str(i): 2 for i in range(1,10)},
    "gad7_responses":  {str(i): 2 for i in range(1,8)},
    "pss10_responses": {str(i): 3 for i in range(1,11)},
}
r = requests.post(f"{API}/ml/predict", json=ml_body, headers=H, timeout=10)
check("ML /predict 200",       r.status_code == 200, r.text[:60])
if r.status_code == 200:
    ml = r.json()
    check("risk_label present",    "risk_label" in ml)
    check("confidence present",    "confidence" in ml)
    check("shap_features present", "shap_features" in ml)
    print(f"     -> {ml.get('risk_label')} @ {(ml.get('confidence') or 0)*100:.1f}%  SHAP: {list(ml.get('shap_features',{}).keys())[:2]}")

# 5. Summary
section("PHASE 8 QUICK SMOKE TEST SUMMARY")
total = PASS + FAIL
print(f"\n  PASSED: {PASS}/{total}   FAILED: {FAIL}/{total}")
if FAIL == 0:
    print("  *** ALL QUICK CHECKS PASSED ***")
else:
    print(f"  {FAIL} item(s) failed")
    sys.exit(1)
