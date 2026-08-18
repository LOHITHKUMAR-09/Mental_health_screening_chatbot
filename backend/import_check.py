import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

print("Checking all imports...")
from app.core.config import settings
from app.core.database import engine, Base, db_url
from app.models.user import User
from app.models.session import Session
from app.models.screening_response import ScreeningResponse
from app.models.risk_score import RiskScore
from app.models.crisis_event import CrisisEvent
from app.core.security import create_access_token, verify_password, get_password_hash
from app.screening.scorers import PHQ9Scorer, GAD7Scorer, PSS10Scorer, CompositeRiskCalculator
from app.crisis.detector import crisis_detector
from app.chatbot.screening_flow import get_next_question, parse_likert_response
from app.api.v1.router import api_router

print(f"DB URL: {db_url[:60]}...")
print(f"Tables registered: {list(Base.metadata.tables.keys())}")
print("ALL IMPORTS OK")
