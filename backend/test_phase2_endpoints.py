import httpx
import json
import time
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api/v1"

def test_suite():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    print("=" * 60)
    print("PHASE 2 BACKEND COMPREHENSIVE VERIFICATION")
    print("=" * 60)

    # 1. Health check
    res = client.get("http://localhost:8000/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] 1. Root & Health Check Endpoint")

    # 2. Register new user
    user_email = f"student_{int(time.time())}@university.edu"
    reg_payload = {
        "email": user_email,
        "password": "Password123!",
        "full_name": "Screening Test Student",
        "year_of_study": 3,
        "major": "Computer Science"
    }
    res = client.post("/auth/register", json=reg_payload)
    assert res.status_code == 201, f"Registration failed: {res.text}"
    reg_data = res.json()
    assert "access_token" in reg_data
    print(f"[PASS] 2. User Registration (email={user_email}, role={reg_data['role']})")

    # 3. Login
    login_payload = {"email": user_email, "password": "Password123!"}
    res = client.post("/auth/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 3. User Login & JWT Generation")

    # 4. Anonymous Session creation
    res = client.post("/auth/anonymous")
    assert res.status_code == 201, f"Anonymous auth failed: {res.text}"
    anon_data = res.json()
    assert anon_data["is_anonymous"] is True
    print(f"[PASS] 4. Anonymous Session Auth (user_id={anon_data['user_id']})")

    # 5. Start Session
    res = client.post("/sessions/start", headers=auth_headers)
    assert res.status_code == 201, f"Start session failed: {res.text}"
    sess_data = res.json()
    session_id = sess_data["session_id"]
    print(f"[PASS] 5. Session Created (session_id={session_id}, state={sess_data['current_state']})")

    # 6. Get Session State
    res = client.get(f"/sessions/{session_id}")
    assert res.status_code == 200, f"Get session failed: {res.text}"
    assert res.json()["current_state"] == "greeting"
    print("[PASS] 6. Get Session State")

    # 7. Conversational Chat flow: greeting -> consent -> background -> phq9
    chat_res = client.post("/chat/message", json={"session_id": session_id, "message": "Hello MindEase"})
    assert chat_res.status_code == 200
    assert chat_res.json()["current_state"] == "consent"
    print("  [Chat] Greeting -> Consent:", chat_res.json()["bot_message"][:60].strip(), "...")

    chat_res = client.post("/chat/message", json={"session_id": session_id, "message": "Yes, I agree and give consent"})
    assert chat_res.status_code == 200
    assert chat_res.json()["current_state"] == "background"
    print("  [Chat] Consent -> Background:", chat_res.json()["bot_message"][:60].strip(), "...")

    chat_res = client.post("/chat/message", json={"session_id": session_id, "message": "I am a 3rd year engineering student"})
    assert chat_res.status_code == 200
    assert chat_res.json()["current_state"] == "phq9"
    print("  [Chat] Background -> PHQ9 Start:", chat_res.json()["bot_message"][:60].strip(), "...")
    print("[PASS] 7. Conversational Flow & State Transitions")

    # 8. Complete PHQ-9 (9 items), GAD-7 (7 items), PSS-10 (10 items)
    print("  [Chat] Answering PHQ-9 items...")
    for i in range(1, 10):
        chat_res = client.post("/chat/message", json={"session_id": session_id, "message": "1"})
        assert chat_res.status_code == 200

    print("  [Chat] Answering GAD-7 items...")
    for i in range(1, 8):
        chat_res = client.post("/chat/message", json={"session_id": session_id, "message": "2"})
        assert chat_res.status_code == 200

    print("  [Chat] Answering PSS-10 items...")
    for i in range(1, 11):
        chat_res = client.post("/chat/message", json={"session_id": session_id, "message": "2"})
        assert chat_res.status_code == 200

    print(f"  [Chat] Final State: {chat_res.json()['current_state']}, Screening complete: {chat_res.json()['screening_complete']}")
    print("[PASS] 8. Full 26-Question Questionnaire Completion via Chat")

    # 9. Results endpoint
    res = client.get(f"/results/{session_id}")
    assert res.status_code == 200, f"Results failed: {res.text}"
    results = res.json()
    print(f"  [Results] PHQ-9: {results['phq9_score']} ({results['phq9_severity']})")
    print(f"  [Results] GAD-7: {results['gad7_score']} ({results['gad7_severity']})")
    print(f"  [Results] PSS-10: {results['pss10_score']} ({results['pss10_severity']})")
    print(f"  [Results] Composite Risk: {results['rule_based_risk']}")
    print(f"  [Results] Coping suggestions count: {len(results['coping_suggestions'])}")
    print("[PASS] 9. Scoring & Results Endpoint with Coping Suggestions")

    # 10. Direct screening item submission & scoring endpoints
    res = client.post("/screening/submit-item", json={
        "session_id": session_id,
        "instrument": "phq9",
        "item_number": 1,
        "response_value": 3
    })
    assert res.status_code == 201, f"Direct item submit failed: {res.text}"

    score_res = client.get(f"/screening/{session_id}/score/phq9")
    assert score_res.status_code == 200
    print(f"[PASS] 10. Direct Screening Item & Score Endpoint (phq9_score={score_res.json()['total_score']})")

    # 11. Crisis Detection
    crisis_res = client.post("/chat/message", json={
        "session_id": session_id,
        "message": "I want to kill myself and end it all"
    })
    assert crisis_res.status_code == 200
    assert crisis_res.json()["is_crisis"] is True
    assert crisis_res.json()["crisis_resources"] is not None
    print(f"[PASS] 11. Crisis Detection Guardrail Triggered (Helplines Included)")

    # 12. Complete Session
    res = client.post(f"/sessions/{session_id}/complete")
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    print("[PASS] 12. Session Mark Completed")

    print("\n" + "=" * 60)
    print("ALL 12 BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

test_suite()
