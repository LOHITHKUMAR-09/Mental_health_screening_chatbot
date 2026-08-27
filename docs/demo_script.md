# MindEase — Review 1 Demo Script

> Estimated time: 8–10 minutes

---

## Pre-Demo Checklist

Before presenting, ensure:
- [ ] PostgreSQL 16 service is running
- [ ] Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (from `backend/`)
- [ ] Frontend: `npm run dev` (from `frontend/`) → http://localhost:5173
- [ ] Browser tab open at http://localhost:5173
- [ ] Browser tab open at http://localhost:8000/docs
- [ ] Terminal ready in backend/ for live test

---

## Demo Flow

### Step 1 — Project Intro (1 min)
> "MindEase is a mental health screening chatbot designed for university students. It administers three validated clinical instruments — PHQ-9 for depression, GAD-7 for anxiety, and PSS-10 for stress — through a natural conversational interface, then uses a trained ML model to classify the student's risk level."

Show the **architecture diagram** (`docs/diagrams/architecture.md`).

---

### Step 2 — Live Chat Demo (3–4 min)

Open http://localhost:5173

1. **Home page** — point out the disclaimer and "Start Screening" CTA
2. Click **Start Screening** → anonymous session begins
3. Show the **Greeting** state — bot welcomes the student warmly
4. Show the **Consent** screen — type "I agree to participate"
5. Show **Background collection** — type "I am a 2nd year student, feeling overwhelmed lately"
6. **PHQ-9 starts** — point out the Likert quick-select buttons (0–3 options)
   - Select answers using the buttons for a few questions; narrate what each item measures
   - Mention: "Question 9 is the suicidal ideation item — it feeds directly into crisis detection"
7. Advance through **GAD-7** quickly (use button clicks)
8. Show **PSS-10** — note reverse-scoring on items 4, 5, 7, 8

---

### Step 3 — Crisis Detection Demo (1 min)

> "Before any message reaches the LLM, it passes through our crisis detector."

In a **new incognito tab**:
1. Start a fresh session
2. Type: **"I want to end my life"**
3. Show the **red crisis alert banner** appearing in the chat
4. Read out the helpline numbers: iCall, Vandrevala, 112
5. Type: **"main mar jana chahta hun"** (Hinglish)
6. Crisis triggers again — show Hinglish detection is working

> "This runs 100% deterministically — no LLM involvement in the crisis response."

---

### Step 4 — Results Page (2 min)

After completing all 26 questions:

1. Results page auto-loads showing the **3-panel score grid**:
   - PHQ-9 score + severity badge (green/yellow/orange/red)
   - GAD-7 score + severity badge
   - PSS-10 score + stress level
2. Show **ML Risk Label** — Low / Moderate / High with confidence %
3. Show **SHAP feature tags** — "These are the top features driving the ML prediction"
4. Show **Coping Suggestions** — personalized based on risk level
5. Show **Emergency Contacts** — always present at bottom

> "The ML model is a Random Forest trained on 1000 synthetic samples matching published clinical distributions — 39 features including all item scores plus derived features like variance and severe-item count."

---

### Step 5 — API Docs (1 min)

Open http://localhost:8000/docs

> "FastAPI auto-generates interactive docs. Let me show the key endpoints."

- Expand `POST /api/v1/chat/message` — show request/response schema
- Expand `GET /api/v1/sessions/{id}/results` — show the full response including ML fields
- Expand `POST /api/v1/ml/predict` — the direct ML inference endpoint
- Try a **live API call** via Swagger UI:
  - POST `/health` → shows database connected

---

### Step 6 — Run Automated Tests (1 min)

In terminal:
```bash
cd backend
python test_phase8_e2e.py
```

All checks pass — show the output live.

---

## Key Talking Points

| Topic | What to say |
|---|---|
| **Not a diagnosis tool** | "MindEase is a screening tool. Results flag students who may benefit from professional support — not a clinical diagnosis." |
| **Privacy** | "Anonymous sessions require no email. Registered users get persistent history. All data stays on-premise." |
| **Crisis safety** | "The crisis detector runs before the LLM on every single message. The response is hard-coded — never AI-generated." |
| **ML explainability** | "SHAP values tell the student *why* they received their risk label — which items contributed most." |
| **Hinglish support** | "University students often mix Hindi and English. The detector handles both." |

---

## What is NOT in Review 1 (Coming in Review 2)

- Counselor Dashboard (student queue, population analytics)
- MentalBERT NLP features for text-based ML
- RAG psychoeducation engine (LangChain + pgvector)
- Longitudinal tracking across sessions
- Cloud deployment (GCP/AWS)

---

## Backup: If demo breaks

Run the automated test as fallback:
```bash
python test_phase8_e2e.py
```

Show the test output — it covers all 5 verification sections automatically.
