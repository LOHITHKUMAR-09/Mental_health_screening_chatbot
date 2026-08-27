import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

try:
    from app.main import app
    print("app import: OK")
except Exception as e:
    import traceback
    traceback.print_exc()
