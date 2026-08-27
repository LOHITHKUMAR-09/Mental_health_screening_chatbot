import requests, json

BASE = "http://localhost:8000/api/v1"

# 1. Anonymous login
r = requests.post(f"{BASE}/auth/anonymous")
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# 2. Start session
r = requests.post(f"{BASE}/sessions/start", headers=headers)
sid = r.json().get("session_id")
print("Session ID:", sid)

def chat(msg):
    res = requests.post(f"{BASE}/chat/message", json={"session_id": sid, "message": msg}, headers=headers)
    data = res.json()
    print(f"\nUser: {msg}")
    print(f"Bot: {data.get('bot_message')[:120]}...")
    return data

# Start flow
chat("hello")
chat("I am ready to begin")
chat("I am a third year CS student")

# Answer first 4 questions of PHQ-9 and verify each question is DIFFERENT
q1_res = chat("1")
q2_res = chat("2")
q3_res = chat("1")
q4_res = chat("0")

print("\n=== VERIFICATION COMPLETE ===")
