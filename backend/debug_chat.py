import httpx
import sys
sys.stdout.reconfigure(encoding="utf-8")

client = httpx.Client(base_url="http://localhost:8000/api/v1")
s = client.post("/sessions/start").json()
sid = s["session_id"]
print("Initial session state:", s["current_state"])

r1 = client.post("/chat/message", json={"session_id": sid, "message": "hello"}).json()
print("Call 1 state:", r1["current_state"], "| bot:", r1["bot_message"][:40])

# Check DB state
s_check = client.get(f"/sessions/{sid}").json()
print("DB state after call 1:", s_check["current_state"])

r2 = client.post("/chat/message", json={"session_id": sid, "message": "Yes, I agree and give consent"}).json()
print("Call 2 state:", r2["current_state"], "| bot:", r2["bot_message"][:40])
