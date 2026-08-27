import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

print("=== BACKEND IMPORT CHECK ===")
modules = [
    "app.core.config",
    "app.core.database",
    "app.models.user",
    "app.models.session",
    "app.models.screening_response",
    "app.models.risk_score",
    "app.models.crisis_event",
    "app.models.message",
    "app.screening.scorers",
    "app.crisis.detector",
    "app.chatbot.scripted_responses",
    "app.chatbot.conversation_engine",
    "app.ml.predictor",
    "app.api.v1.router",
]
failed = []
for m in modules:
    try:
        __import__(m)
        print(f"  OK  {m}")
    except Exception as e:
        print(f"  FAIL {m}: {e}")
        failed.append(m)
print()
if not failed:
    print("ALL IMPORTS CLEAN")
else:
    print(f"FAILED: {failed}")
