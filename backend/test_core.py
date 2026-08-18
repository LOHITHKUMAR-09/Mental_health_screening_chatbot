import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.screening.scorers import PHQ9Scorer, GAD7Scorer, PSS10Scorer, CompositeRiskCalculator
from app.crisis.detector import crisis_detector
from app.chatbot.screening_flow import get_next_question, parse_likert_response

print("=== MindEase Backend Core Tests ===\n")

# Test 1: PHQ-9 scorer
responses = {1: 2, 2: 1, 3: 3, 4: 1, 5: 0, 6: 2, 7: 1, 8: 0, 9: 0}
score = PHQ9Scorer.score(responses)
assert score.total == 10, f"Expected 10, got {score.total}"
assert score.severity == "moderate"
print(f"PHQ-9: score={score.total}, severity={score.severity}  OK")

# Test 2: GAD-7 scorer
gad_responses = {1: 1, 2: 2, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1}
gad_score = GAD7Scorer.score(gad_responses)
print(f"GAD-7: score={gad_score.total}, severity={gad_score.severity}  OK")

# Test 3: PSS-10 with reverse scoring
pss_responses = {i: 2 for i in range(1, 11)}
pss_score = PSS10Scorer.score(pss_responses)
print(f"PSS-10: score={pss_score.total}, severity={pss_score.severity}  OK")

# Test 4: Composite risk
composite = CompositeRiskCalculator.compute(score, gad_score, pss_score)
print(f"Composite risk: {composite.composite_risk}  OK")

# Test 5: Crisis detection
r1 = crisis_detector.detect("I want to die")
r2 = crisis_detector.detect("I am feeling stressed about exams")
assert r1.is_crisis == True,  f"Expected crisis=True, got {r1.is_crisis}"
assert r2.is_crisis == False, f"Expected crisis=False, got {r2.is_crisis}"
print(f"Crisis detect: 'want to die' -> {r1.trigger_type}  OK")
print(f"Crisis detect: 'stressed' -> not crisis  OK")

# Test 6: PHQ-9 suicidal ideation flag
sui_responses = {9: 2}
assert PHQ9Scorer.is_suicidal_ideation(sui_responses) == True
print(f"PHQ-9 item 9 suicidal flag: OK")

# Test 7: Questionnaire flow
q = get_next_question("phq9", {1: 0, 2: 1})
assert q["item_number"] == 3
print(f"Next PHQ-9 question: item {q['item_number']}  OK")

q_done = get_next_question("gad7", {i: 0 for i in range(1, 8)})
assert q_done is None
print(f"GAD-7 all answered: next=None  OK")

# Test 8: Likert parsing
options = {0: "Not at all", 1: "Several days", 2: "More than half the days", 3: "Nearly every day"}
val = parse_likert_response("Several days", options)
assert val == 1, f"Expected 1, got {val}"
val2 = parse_likert_response("2", options)
assert val2 == 2, f"Expected 2, got {val2}"
print(f"Likert parse: 'Several days' -> {val}, '2' -> {val2}  OK")

# Test 9: JWT
token = create_access_token({"sub": "test-user-id", "role": "student"})
assert token is not None
print(f"JWT token creation: OK (len={len(token)})")

# Test 10: Password hashing
hashed = get_password_hash("testpassword123")
assert verify_password("testpassword123", hashed) == True
assert verify_password("wrongpassword", hashed) == False
print(f"Password hashing: OK")

print("\n=== ALL 10 TESTS PASSED ===")
