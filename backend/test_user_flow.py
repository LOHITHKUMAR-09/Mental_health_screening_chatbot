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
    print(f"Bot [{data.get('current_state')}]: {data.get('bot_message')}")
    return data

# Test exact sequence
chat("hello")
chat("are you busy")
chat("i am in third year")
chat("nothing on my mind")
chat("1")
chat("2")
