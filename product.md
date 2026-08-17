# 🧠 ML-Assisted Mental Health Screening Chatbot — Product Specification

> **Project:** ML-Assisted Mental Health Screening Chatbot for University Students
> **Review Target:** 40–50% completion (Review 1)
> **Timeline:** 4 months
> **Target Users:** University students (ages 18–25) with subclinical to moderate distress

---

## 🎯 Product Vision

A safe, empathic, and privacy-first mental health screening chatbot that helps university students reflect on their wellbeing, receive a structured risk assessment, and connect with campus counseling services — acting as a **bridge, not a replacement**, for professional mental health care.

---

## 📐 System Architecture Overview

`
┌────────────────────────────────────────────────────────────┐
│                   STUDENT FRONTEND (React)                 │
│        Chat UI · Consent Modal · Results Page              │
└─────────────────────────┬──────────────────────────────────┘
                          │ HTTPS / WebSocket
┌─────────────────────────▼──────────────────────────────────┐
│                  FASTAPI BACKEND (Python)                   │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Guardrail   │  │  Conversation  │  │ Clinical Score │  │
│  │  Layer       │  │  Engine (LLM)  │  │ Engine (ML)    │  │
│  │  (Crisis Det)│  │  + RAG         │  │ XGBoost/RF     │  │
│  └──────────────┘  └────────────────┘  └────────────────┘  │
└───────────┬────────────────────┬───────────────────────────┘
            │                    │
  ┌─────────▼────────┐  ┌────────▼──────────┐
  │   PostgreSQL DB  │  │  Vector DB        │
  │  (pgvector)      │  │  (CBT Knowledge   │
  │  Users · Scores  │  │   Base for RAG)   │
  └──────────────────┘  └───────────────────┘
            │
  ┌─────────▼──────────────┐
  │  COUNSELOR DASHBOARD   │
  │  (React Admin Panel)   │
  └────────────────────────┘
`

---

## 🧩 Core Features (Full Product)

### 1. 🤖 Conversational Chatbot Interface

| Feature | Description |
|---|---|
| **Empathic Dialogue** | LLM-powered (GPT-4o / Llama 3 via RAG) empathic conversational flow with a "supportive listener" persona |
| **Conversational Screening** | PHQ-9, GAD-7, PSS-10 questionnaires interleaved naturally into chat — not interrogation-style |
| **Multi-turn Memory** | Maintains context over the screening session using LangGraph stateful memory |
| **Tone and Style** | Non-judgmental, simple English, culturally sensitive language for Indian university students |
| **Anonymous Usage** | Optional anonymous mode — no login required for basic screening |
| **Multilingual** | Base: English. Planned: Hindi/regional language support |

### 2. 🧪 Mental Health Screening Engine

| Instrument | Domain | Items | Score Range | Risk Cutoffs |
|---|---|---|---|---|
| **PHQ-9** | Depression | 9 | 0–27 | 5=Mild, 10=Moderate, 15=Mod-Severe, 20=Severe |
| **GAD-7** | Anxiety | 7 | 0–21 | 5=Mild, 10=Moderate, 15=Severe |
| **PSS-10** | Stress | 10 | 0–40 | ≤13=Low, 14–26=Moderate, ≥27=High |
| **WEMWBS** | Wellbeing | 14 | 14–70 | <41=Low Wellbeing |

- **Deterministic Scoring:** Questionnaire scoring is hardcoded, completely isolated from the LLM layer to ensure 100% accuracy.
- **Composite Risk Level:** Low / Moderate / High computed from combined subscale scores.

### 3. 🤖 ML Risk Classification Module

**Goal:** Classify student into Low / Moderate / High distress using ML models trained on questionnaire responses.

**Feature Set:**
- Individual item scores (PHQ-9 × 9, GAD-7 × 7, PSS-10 × 10)
- Subscale totals (depression score, anxiety score, stress score)
- Composite features: score deltas, sum of severe-domain items
- Contextual features: time-of-day, session frequency, is returning user
- NLP-derived features (if open-text collected): first-person pronoun ratio, sentiment score (VADER/BERT), absolutist word count, emotional valence
- Demographic features (optional, with consent): year of study, major

**Models to Train and Benchmark:**

| Model | Expected Accuracy | Interpretability |
|---|---|---|
| Logistic Regression | ~75–80% | Very High |
| Random Forest | ~85–92% | High (feature importance) |
| XGBoost | ~87–95% | High (with SHAP) |
| LightGBM | ~87–94% | High |
| SVM (RBF kernel) | ~80–88% | Low |
| MentalBERT (NLP) | ~85–92% | Medium (attention maps) |

**Best Model:** Ensemble of XGBoost + MentalBERT for highest accuracy with explainability via SHAP values.

**Evaluation Protocol:**
- Stratified K-Fold Cross Validation (k=5)
- Metrics: Accuracy, Macro F1, Precision, Recall per class, Confusion Matrix, AUC-ROC
- Fairness evaluation across demographic groups

### 4. 🚨 Crisis Detection System (Safety-Critical)

This module bypasses the LLM entirely and uses deterministic logic + a fast classifier.

**Architecture:**
1. **Layer 1 – Regex/Keyword Triggers:** Hard-coded patterns for suicidal ideation ("want to die", "end my life", "kill myself")
2. **Layer 2 – ML Classifier:** RoBERTa-based fine-tuned classifier running parallel to the LLM on every user message
3. **Layer 3 – Escalation Response:** Hard-coded crisis response with:
   - iCall helpline: 9152987821
   - Vandrevala Foundation Lifeline: 1860-2662-345
   - Campus emergency contact
   - "Reach out to a counselor NOW" CTA

### 5. 📊 Counselor Dashboard

| Feature | Details |
|---|---|
| **Student Risk Queue** | Red/Yellow/Green triage list sorted by risk severity |
| **Individual Student View** | PHQ-9, GAD-7, PSS trends over time (line charts) |
| **Population Analytics** | Heatmaps of stress spikes (exam weeks), radar charts across domains |
| **SHAP Explainability** | Highlights which responses drove the risk classification |
| **Crisis Alerts** | Real-time notification when a student triggers crisis detection |
| **Session Management** | Schedule follow-up, assign CBT exercises, add counselor notes |
| **Anonymized Export** | Aggregate CSV export for institutional mental health reports |

### 6. 🔒 Ethics, Privacy and Security

| Requirement | Implementation |
|---|---|
| **Informed Consent** | Full-screen consent modal before screening — cannot be skipped |
| **Data Anonymization** | Microsoft Presidio for PII stripping from text before ML inference |
| **Role-Based Access** | Students see only their own data; counselors see assigned students only |
| **Encryption** | AES-256 at rest, TLS 1.3 in transit |
| **Data Minimization** | Retain only clinical scores + embeddings, not raw chat transcripts (configurable) |
| **Non-Diagnostic Disclaimer** | Persistent visible disclaimer throughout all interactions |
| **Right to Delete** | Students can delete all their data at any time |

### 7. 📬 Psychoeducation and Resource Engine

- Personalized CBT-based coping suggestions based on risk score and domain (anxiety vs. depression vs. stress)
- Static resource library: breathing exercises, sleep hygiene, mindfulness guides
- Dynamic RAG-based recommendations pulled from vetted psychological knowledge base
- University counseling center booking links, location, contact info

---

## 🏗️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React (TypeScript) + Tailwind CSS | Responsive, accessible chat UI |
| **Chat UI Library** | ChatScope UI Kit / Custom | Smooth conversation UX |
| **Backend** | Python + FastAPI | Async, native ML ecosystem, high performance |
| **LLM Orchestration** | LangChain + LangGraph | Stateful multi-turn conversation management + RAG |
| **LLM Provider** | OpenAI GPT-4o / Groq (Llama 3) | GPT-4o for quality; Groq for speed + cost |
| **ML Models** | scikit-learn, XGBoost, LightGBM, HuggingFace Transformers (MentalBERT) | Full ML experimentation |
| **Explainability** | SHAP | Clinical trust and counselor dashboard |
| **Primary Database** | PostgreSQL + pgvector | Structured data + vector embeddings in one place |
| **Crisis Classifier** | RoBERTa fine-tuned (HuggingFace) | Fast, accurate crisis detection |
| **PII Anonymizer** | Microsoft Presidio | Privacy compliance |
| **Auth** | JWT + OAuth2 | Secure sessions |
| **Containerization** | Docker + Docker Compose | Reproducible deployments |
| **Testing** | pytest, React Testing Library | Backend + frontend coverage |

---

## 🗺️ Conversation Flow Design

`
[START]
  │
  ▼
Greeting and Persona Introduction
  │
  ▼
Informed Consent Modal (must accept)
  │
  ▼
Optional: Background Questions (year, academic stress context)
  │
  ▼
Screening Phase (PHQ-9 → GAD-7 → PSS-10 interleaved in conversation)
  │  ← Crisis Detection runs on EVERY user message simultaneously →
  │
  │  If crisis triggered → Hard-coded crisis response + resources [STOP]
  │
  ▼
Score Computation (deterministic, isolated from LLM)
  │
  ▼
ML Risk Classification (XGBoost + SHAP)
  │
  ▼
Results Page:
  ├── "Your responses suggest moderate stress and mild anxiety."
  ├── Personalized coping suggestions (RAG-grounded)
  ├── University counseling center link + booking
  └── Option: Share anonymized results with counselor (with consent)
  │
[END SESSION]
`

---

## 📦 Datasets and Open-Source Resources

| Dataset | Source | Use |
|---|---|---|
| **DAIC-WOZ** | USC ICT (requires application) | Depression detection from transcripts |
| **SMHD (Reddit)** | Zenodo | NLP model pre-training |
| **MentalChat16K** | HuggingFace | Empathetic dialogue training |
| **CLPsych Shared Tasks** | CLPsych Workshop | Suicidality detection (controlled access) |
| **Kaggle Mental Health Survey** | Kaggle | Tabular ML benchmarking |
| **Synthetic Data** | Generated from published distributions | Augmenting small pilot dataset |

---

## 🏁 Review 1 Deliverables (40–50% of Project)

The first review should demonstrate a working, end-to-end skeleton of the core product.

### Must Be Complete by Review 1

1. **Project Setup and Architecture**
   - Monorepo structure with frontend/, backend/, ml/, docs/
   - Docker Compose with all services running locally
   - Environment management (.env, secrets)

2. **Backend Core**
   - FastAPI app with all route stubs
   - PostgreSQL schema (users, sessions, screening_responses, risk_scores)
   - JWT Auth: Student login/register + anonymous session
   - Conversation session management API

3. **Chatbot Frontend (Web)**
   - Full chat UI (React) with responsive design
   - Consent modal flow
   - Questionnaire delivery (all 3 instruments embedded in chat)
   - Results display page with risk level

4. **Screening Engine**
   - PHQ-9, GAD-7, PSS-10 deterministic scoring logic (Python module)
   - Composite risk level computation (Low/Moderate/High)

5. **ML Pipeline v1**
   - Data collection script / synthetic dataset generation
   - Feature engineering pipeline (scikit-learn Pipeline)
   - Baseline models trained: Logistic Regression, Random Forest, XGBoost
   - Evaluation notebook with metrics (accuracy, F1, confusion matrix)
   - SHAP explanations for XGBoost

6. **Basic LLM Chatbot**
   - LangChain integration with GPT-4o (or Groq Llama 3)
   - System prompt defining empathic persona + strict guardrails
   - Questionnaire interleaved into conversation flow

7. **Crisis Detection (Basic)**
   - Keyword/regex-based detection layer
   - Hard-coded crisis response with helpline numbers

8. **Documentation**
   - README with setup instructions
   - API documentation (FastAPI auto-docs / Swagger)
   - Architecture diagram

### Review 2 Targets (Remaining 50–60%)

- Full ML model improvement (LightGBM, MentalBERT NLP)
- Advanced RAG-based psychoeducation engine
- Counselor dashboard (React admin panel)
- SHAP explainability views in dashboard
- ML classifier-based crisis detection (RoBERTa)
- PII anonymization (Microsoft Presidio)
- User history and longitudinal tracking
- Final testing, security hardening, deployment

---

## 📂 Recommended Project Folder Structure

`
ML_Mental_Health_Screening/
├── frontend/               # React + TypeScript app
│   ├── src/
│   │   ├── components/     # ChatWindow, ConsentModal, ResultsCard
│   │   ├── pages/          # Home, Chat, Results, Login
│   │   ├── hooks/          # useChat, useAuth
│   │   └── api/            # Axios API clients
│   └── package.json
│
├── backend/                # FastAPI Python app
│   ├── app/
│   │   ├── api/            # Route handlers
│   │   ├── core/           # Auth, config, security
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── screening/      # PHQ-9, GAD-7, PSS-10 scoring logic
│   │   ├── crisis/         # Crisis detection module
│   │   └── chatbot/        # LangChain / LLM orchestration
│   ├── requirements.txt
│   └── Dockerfile
│
├── ml/                     # ML experimentation and models
│   ├── notebooks/          # Jupyter notebooks (EDA, training, eval)
│   ├── data/               # Datasets (raw, processed, synthetic)
│   ├── features/           # Feature engineering scripts
│   ├── models/             # Trained model artifacts (.pkl, .json)
│   └── evaluate.py         # Evaluation scripts
│
├── dashboard/              # Counselor dashboard (React admin)
│   └── src/
│
├── docs/                   # Architecture diagrams, research notes
├── docker-compose.yml
├── .env.example
├── README.md
├── product.md              # This file
└── todo.md                 # Task tracking
`

---

## 🔬 Key Research References

1. PHQ-9 and GAD-7 validated instruments — Kroenke and Spitzer (2001, 2006)
2. MentalBERT — Ji et al. (2021) — Pre-trained BERT for mental health NLP
3. XGBoost for PHQ-9 classification — 83% accuracy on mindfulness datasets
4. Random Forest — up to 97% accuracy on DASS-21 severity classification
5. LangGraph for stateful mental health chatbots
6. SHAP for clinical explainability in ML models
7. Microsoft Presidio for PII anonymization
8. CLPsych 2024 — LLMs for suicidality risk detection in Reddit posts
9. MentalChat16K — HuggingFace dataset for empathetic mental health dialogue
10. Systematic reviews: Chatbot-Delivered Interventions for Mental Health Among Young People (meta-analysis, 2024)
