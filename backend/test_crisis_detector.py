"""Unit tests for enhanced crisis detector (Phase 5)."""
import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

from app.crisis.detector import KeywordCrisisDetector

detector = KeywordCrisisDetector()
passed = 0
failed = 0

def test(text, should_be_crisis, label=""):
    global passed, failed
    result = detector.detect(text)
    is_crisis = result.is_crisis
    ok = is_crisis == should_be_crisis
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    symbol = "OK" if ok else "XX"
    print(f"  [{status}] {symbol} {'CRISIS' if should_be_crisis else 'SAFE  '} | {label or text[:50]}")

print("=== CRISIS DETECTOR UNIT TESTS ===\n")
print("[English Crisis Phrases]")
test("I want to kill myself", True, "kill myself")
test("I'm thinking about suicide", True, "suicide")
test("I don't want to live anymore", True, "don't want to live anymore")
test("I am going to end my life tonight", True, "end my life tonight")
test("I have been having thoughts of self-harm", True, "self-harm thoughts")

print("\n[Hinglish Crisis Phrases]")
test("main khud ko khatam karna chahta hun", True, "Hinglish: khatam karna chahta")
test("mujhe jeene ka mann nahi", True, "Hinglish: jeene ka mann nahi")
test("main mar jana chahta hun", True, "Hinglish: mar jana chahta")

print("\n[Safe Phrases (should NOT trigger)]")
test("I am killing it at this exam", False, "killing it at exam")
test("this assignment is killing me", False, "assignment killing me")
test("I want to kill this bug in my code", False, "kill the bug")
test("I am so stressed about my exams", False, "stressed about exams")
test("I feel really down today", False, "feel down today")
test("life is hard sometimes", False, "life is hard")

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL CRISIS DETECTOR TESTS PASSED")
else:
    print(f"WARNING: {failed} tests failed")
    sys.exit(1)
