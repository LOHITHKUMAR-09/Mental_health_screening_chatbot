# 🧠 MindEase — ML-Assisted Mental Health Screening Chatbot

> An empathic, privacy-first mental health screening chatbot for university students.  
> Built with FastAPI · React · PostgreSQL · LangChain · XGBoost · SHAP

---

## 📋 Project Overview

MindEase is a final-year project building an **ML-assisted mental health screening chatbot** for university students. It conducts validated screening (PHQ-9, GAD-7, PSS-10), classifies distress risk using machine learning, and connects students with campus counseling resources.

> ⚠️ **This is a screening tool only. Not a clinical diagnosis system. Not a replacement for professional mental health care.**

---

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- Docker Desktop
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### 1. Clone and configure
`ash
git clone <repo-url>
cd ML_Mental_Health_Screening
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY or GROQ_API_KEY
`

### 2. Start all services
`ash
docker compose up --build
`

| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

---

## 🏗️ Project Structure

`
ML_Mental_Health_Screening/
├── frontend/              # React + TypeScript (Vite)
├── backend/               # FastAPI + SQLAlchemy
│   └── app/
│       ├── api/v1/        # REST endpoints
│       ├── core/          # Config, DB, Security
│       ├── models/        # SQLAlchemy ORM models
│       ├── screening/     # PHQ-9, GAD-7, PSS-10 scorers
│       ├── crisis/        # Crisis detection module
│       └── chatbot/       # LangChain LLM integration
├── ml/                    # ML experimentation (Jupyter + scripts)
│   ├── data/              # Datasets (synthetic + real)
│   ├── features/          # Feature engineering
│   ├── notebooks/         # Training + evaluation notebooks
│   └── models/            # Saved model artifacts
├── dashboard/             # Counselor dashboard (Phase 2)
├── docs/                  # Architecture diagrams + research
├── docker-compose.yml
└── .env.example
`

---

## 🧪 Screening Instruments

| Instrument | Domain | Items | Score Range |
|---|---|---|---|
| PHQ-9 | Depression | 9 | 0–27 |
| GAD-7 | Anxiety | 7 | 0–21 |
| PSS-10 | Stress | 10 | 0–40 |

---

## 🤖 ML Pipeline

- **Features:** 26 questionnaire item scores + derived features + contextual signals
- **Models:** Logistic Regression, Random Forest, XGBoost (primary), LightGBM
- **Explainability:** SHAP values for clinical interpretability
- **Target:** Low / Moderate / High distress classification

---

## 🚨 Crisis Detection

Every user message is scanned by a keyword/regex-based crisis detector **before** reaching the LLM. Any detected crisis trigger returns a hard-coded response with:
- **iCall:** 9152987821 (Mon–Sat, 8am–10pm)
- **Vandrevala Foundation:** 1860-2662-345 (24/7)
- **Emergency:** 112

---

## 🛠️ Local Development (Without Docker)

### Backend
`ash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload
`

### Frontend
`ash
cd frontend
npm install
npm run dev
`

### ML Notebooks
`ash
cd ml
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/
`

---

## 📊 Review 1 Status

| Module | Status |
|---|---|
| Project Setup + Docker | ✅ Complete |
| Backend Core (FastAPI + DB models) | ✅ Complete |
| API Endpoints (stubs) | ✅ Complete |
| Screening Engine (PHQ-9/GAD-7/PSS-10) | ✅ Complete |
| Crisis Detection (keyword layer) | ✅ Complete |
| Frontend (React pages) | ✅ Complete |
| ML Feature Engineering | ✅ Complete |
| Synthetic Data Generator | ✅ Complete |
| LLM Integration | 🔜 In Progress |
| ML Model Training | 🔜 Next Phase |

---

## ⚖️ Ethics & Privacy

- Informed consent required before screening begins
- Anonymous mode available (no email required)
- No personal data sent to LLM providers
- Data encryption at rest (AES-256) and in transit (TLS 1.3)
- Non-diagnostic disclaimer displayed throughout

---

## 📚 Key References

1. PHQ-9 — Kroenke & Spitzer (2001)
2. GAD-7 — Spitzer et al. (2006)
3. PSS-10 — Cohen et al. (1983)
4. MentalBERT — Ji et al. (2021)
5. Chatbot interventions for student mental health — Meta-analysis (2024)
