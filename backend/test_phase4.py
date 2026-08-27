import httpx
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE_URL = "http://localhost:8000/api/v1"

def test_phase4():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    print("=" * 60)
    print("PHASE 4 LLM CHATBOT & STREAMING INTEGRATION VERIFICATION")
    print("=" * 60)

    # 1. Start Session
    sess = client.post("/sessions/start").json()
    sid = sess["session_id"]
    print(f"[PASS] 1. Session Initialized (session_id={sid})")

    # 2. Standard Chat message (Greeting -> Consent)
    r1 = client.post("/chat/message", json={"session_id": sid, "message": "Hi MindEase"}).json()
    assert r1["current_state"] == "consent"
    print("[PASS] 2. Standard Chat Message Handling (State:", r1["current_state"], ")")

    # 3. SSE Streaming Endpoint (/chat/stream)
    print("  Testing SSE stream for: 'Yes, I agree' ...")
    chunks = []
    with client.stream("POST", "/chat/stream", json={"session_id": sid, "message": "Yes, I agree"}) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                if "chunk" in data:
                    chunks.append(data["chunk"])

    assembled = "".join(chunks).strip()
    print("  [SSE Stream Output]:", assembled[:70], "...")
    assert len(chunks) > 0, "No chunks received from SSE stream"
    print("[PASS] 3. Server-Sent Events (SSE) Real-Time Chat Streaming")

    # 4. Message History Persistence (/sessions/{id}/messages)
    history_res = client.get(f"/sessions/{sid}/messages")
    assert history_res.status_code == 200
    messages = history_res.json()
    print(f"  Persisted messages count in PostgreSQL: {len(messages)}")
    for m in messages:
        print(f"    - [{m['sender'].upper()} | {m['state']}]: {m['content'][:50]}...")
    assert len(messages) >= 4, "Expected at least 4 stored messages (2 user + 2 bot)"
    print("[PASS] 4. PostgreSQL Conversation History Persistence")

    print("\n" + "=" * 60)
    print("PHASE 4 LLM CHATBOT INTEGRATION 100% VERIFIED!")
    print("=" * 60)

test_phase4()
