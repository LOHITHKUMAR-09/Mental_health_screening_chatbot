# MindEase — ML-Assisted Mental Health Screening Chatbot

> A clinical-grade, conversational mental health screening tool for university students.
> Combines validated psychometric instruments (PHQ-9, GAD-7, PSS-10) with LLM-powered empathic dialogue and ML-based risk classification.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Running (Local)](#setup--running-local)
- [API Reference](#api-reference)
- [ML Model](#ml-model)
- [Crisis Detection](#crisis-detection)
- [Review 1 Status](#review-1-status)

---

## Overview

MindEase guides university students through three validated mental health instruments via a natural conversational interface:

| Instrument | Items | Score Range | Measures |
|---|---|---|---|
| PHQ-9 | 9 | 0–27 | Depression severity |
| GAD-7 | 7 | 0–21 | Anxiety severity |
| PSS-10 | 10 | 0–40 | Perceived stress |

At the end of screening, an ML risk classifier (Random Forest, 39 features) predicts Low / Moderate / High risk and generates SHAP-based explanations alongside personalised coping suggestions.

---

## Architecture

```
Student Browser
     │
     ▼
React + TypeScript (Vite, Tailwind CSS)
     │  REST / SSE
     ▼
FastAPI Backend (Python 3.14, asyncpg)
     ├── Auth (JWT)
     ├── Session & Chat API
     ├── Conversation Engine (LangChain + Groq LLaMA 3)
     ├── Crisis Detector (regex, English + Hinglish, pre-LLM)
     ├── Screening Engine (PHQ9 / GAD7 / PSS10 scorers)
     └── ML Predictor (Random Forest pipeline, SHAP)
          │
          ▼
     PostgreSQL 16 (asyncpg)
     ml/models/best_model.pkl
```

---

## Features

### Review 1 (Current)
- **Conversational Screening** — LLM-guided flow through 26 questions across PHQ-9, GAD-7, PSS-10
- **Likert Quick-Select** — one-tap response buttons (0–3 / 0–4) on the chat UI
- **Real-time Streaming** — Server-Sent Events (SSE) for bot responses
- **Crisis Detection** — regex-based, runs BEFORE LLM on every message; supports Hinglish phrases
- **Crisis Response** — hard-coded, never LLM-generated; includes iCall, Vandrevala Foundation helplines
- **Clinical Scoring** — deterministic PHQ-9, GAD-7, PSS-10 scoring with severity classification
- **ML Risk Classification** — Random Forest (accuracy ~92%), returns risk label + confidence + SHAP top-5 features
- **Results Dashboard** — 3-panel score grid, SHAP explainability tags, personalised coping tips, emergency contacts
- **JWT Auth** — registered + anonymous user flows
- **Chat History** — all messages persisted to PostgreSQL, reloadable

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.14, Uvicorn |
| ORM | SQLAlchemy 2 (async) + asyncpg |
| Database | PostgreSQL 16 |
| LLM | Groq API (LLaMA 3.1 8B / 70B) via LangChain |
| ML | scikit-learn (Random Forest), SHAP, joblib |
| Auth | JWT (python-jose), bcrypt |

---

## Project Structure

```
ML_Mental_Health_Screening/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # auth, chat, sessions, results, screening, ml
│   │   ├── chatbot/            # conversation_engine, screening_flow, scripted_responses
│   │   ├── core/               # config, database, security
│   │   ├── crisis/             # detector.py (KeywordCrisisDetector)
│   │   ├── ml/                 # predictor.py (MLPredictor)
│   │   ├── models/             # SQLAlchemy ORM models (6 tables)
│   │   └── screening/          # PHQ9Scorer, GAD7Scorer, PSS10Scorer, CompositeRisk
│   ├── .env                    # Environment variables (not committed)
│   ├── requirements.txt
│   └── test_phase8_e2e.py      # Full Review 1 E2E test
├── frontend/
│   ├── src/
│   │   ├── pages/              # HomePage, LoginPage, ChatPage, ResultsPage
│   │   ├── api/                # client.ts, chat.ts
│   │   └── types/              # TypeScript interfaces
│   └── package.json
├── ml/
│   ├── data/synthetic/         # 1000-sample synthetic dataset
│   ├── models/                 # best_model.pkl, label_encoder.pkl, shap_feature_importance.json
│   ├── train_models.py         # Training pipeline (RF, LR, XGBoost)
│   └── features/               # feature_engineering.py
└── docs/
    ├── diagrams/architecture.md
    ├── conversation_flow.md
    ├── instruments.md
    └── tech_stack.md
```

---

## Setup & Running (Local)

### Prerequisites
- Python 3.14+
- Node.js 20+
- PostgreSQL 16 (running on localhost:5432)
- Groq API key (https://console.groq.com)

### 1. Database Setup

```sql
-- Run in psql as superuser
CREATE USER mindease_user WITH PASSWORD 'mindease_password';
CREATE DATABASE mindease_db OWNER mindease_user;
GRANT ALL PRIVILEGES ON DATABASE mindease_db TO mindease_user;
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env
# Edit .env: set GROQ_API_KEY, DATABASE_URL, SECRET_KEY

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend auto-creates all 6 tables on first startup.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env            # set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

### 4. Verify Everything Works

```bash
cd backend
python test_phase8_e2e.py
```

---

## API Reference

Interactive docs: **http://localhost:8000/docs** (Swagger UI)
OpenAPI JSON:    **http://localhost:8000/openapi.json**

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT token |
| POST | `/api/v1/auth/anonymous` | Anonymous session |
| POST | `/api/v1/sessions/start` | Start screening session |
| GET  | `/api/v1/sessions/{id}` | Get session state |
| POST | `/api/v1/chat/message` | Send message, get reply |
| POST | `/api/v1/chat/stream` | SSE streaming response |
| GET  | `/api/v1/sessions/{id}/results` | Scores + ML prediction |
| GET  | `/api/v1/sessions/{id}/messages` | Chat history |
| POST | `/api/v1/ml/predict` | Direct ML inference |
| GET  | `/health` | Health + DB check |

---

## ML Model

- **Algorithm:** Random Forest (200 estimators, class_weight=balanced)
- **Training data:** 1000 synthetic samples from published PHQ-9/GAD-7/PSS-10 clinical distributions
- **Features:** 39 — 9 PHQ items + 7 GAD items + 10 PSS items + 13 derived/contextual
- **CV Accuracy:** ~92% (5-fold stratified)
- **Classes:** Low / Moderate / High risk
- **Explainability:** SHAP feature importance (top-5 per prediction)

---

## Crisis Detection

Crisis detection runs **synchronously, before any LLM call**, on every user message.

- **English patterns:** suicide, self-harm, hopelessness (20+ regex patterns)
- **Hinglish patterns:** mar jana, khudkushi, khatam karna, jeene ka mann nahi, etc.
- **False-positive filters:** "killing it at this exam", "this assignment is killing me" → NOT flagged
- **Response:** Hard-coded template with iCall (9152987821), Vandrevala (1860-2662-345), Emergency (112)
- **Logged:** Every crisis event saved to `crisis_events` table

---

## Review 1 Status

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Research & Planning | **100%** |
| Phase 1 | Project Setup | **100%** |
| Phase 2 | Backend Core (12/12 tests) | **100%** |
| Phase 3 | Clinical Scoring Engine | **100%** |
| Phase 4 | LLM Chatbot + SSE Streaming | **100%** |
| Phase 5 | Crisis Detection (14/14 tests) | **100%** |
| Phase 6 | ML Pipeline & Inference | **100%** |
| Phase 7 | Frontend Chat + Results UI | **100%** |
| Phase 8 | Review 1 Polish & Verification | **100%** |

> **Overall Review 1 completion: 100%**

---

## Disclaimer

MindEase is a **screening tool only** and does **not provide clinical diagnosis or treatment**.
Results should be reviewed by a qualified mental health professional.
If you are in crisis, please contact a helpline immediately.

**iCall:** 9152987821 | **Vandrevala Foundation:** 1860-2662-345 | **Emergency:** 112
