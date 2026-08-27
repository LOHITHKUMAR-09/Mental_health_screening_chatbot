import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

errors = []

modules = [
    "app.core.database",
    "app.core.config",
    "app.core.security",
    "app.models.user",
    "app.models.session",
    "app.models.screening_response",
    "app.models.risk_score",
    "app.models.crisis_event",
    "app.api.v1.endpoints.auth",
    "app.api.v1.endpoints.sessions",
    "app.api.v1.endpoints.chat",
    "app.api.v1.endpoints.results",
    "app.chatbot.scripted_responses",
    "app.chatbot.screening_flow",
    "app.crisis.detector",
    "app.screening.scorers",
]

for m in modules:
    try:
        __import__(m)
        print(f"  OK  {m}")
    except Exception as e:
        errors.append((m, str(e)))
        print(f"  ERR {m}: {e}")

print()
if errors:
    print(f"FAILED: {len(errors)} module(s) have import errors")
else:
    print("ALL IMPORTS OK - backend is ready to start")
