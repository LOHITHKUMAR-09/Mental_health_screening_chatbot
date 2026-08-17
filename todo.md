# ✅ TODO — ML Mental Health Screening Chatbot
> Review 1 Target: 40–50% of project complete
> Full timeline: 4 months

---

## 📋 Legend
- [ ] Not started
- [/] In progress
- [x] Done

---

## 🔴 PHASE 0: Research and Planning (Pre-development)

- [ ] Read and fully understand project specification document
- [ ] Study all 4 questionnaire instruments:
  - [ ] PHQ-9 — scoring, items, cutoffs
  - [ ] GAD-7 — scoring, items, cutoffs
  - [ ] PSS-10 — scoring, items, cutoffs
  - [ ] WEMWBS — scoring, items, cutoffs
- [ ] Research MentalBERT (Ji et al., 2021) paper
- [ ] Research LangGraph stateful conversations
- [ ] Study SHAP values for ML explainability
- [ ] Download or generate pilot dataset
  - [ ] Kaggle Mental Health Surveys
  - [ ] Synthetic data generation script
- [ ] Finalize tech stack decisions (GPT-4o vs Groq Llama 3)
- [ ] Create architecture diagram (draw.io or excalidraw)
- [ ] Plan conversation flow scripts for all 3 questionnaires

---

## 🟠 PHASE 1: Project Setup and Infrastructure

- [x] Initialize monorepo folder structure
  - [x] frontend/
  - [x] backend/
  - [x] ml/
  - [x] dashboard/
  - [x] docs/
- [x] Create .env.example with all required environment variables
- [x] Create docker-compose.yml with:
  - [x] PostgreSQL service
  - [x] Backend (FastAPI) service
  - [x] Frontend (React) service (optional for dev)
  - [x] pgAdmin or database viewer (optional)
- [x] Backend: Initialize FastAPI project with folder structure
  - [x] app/api/, app/core/, app/models/, app/screening/, app/crisis/, app/chatbot/
  - [x] Install and configure: fastapi, uvicorn, sqlalchemy, alembic, pydantic, python-jose, passlib
- [x] Frontend: Initialize React + TypeScript project with Tailwind CSS
  - [x] Install: react, typescript, tailwindcss, axios, react-router-dom, @chatscope/chat-ui-kit-react
- [x] ML: Initialize Python environment
  - [x] Install: scikit-learn, xgboost, lightgbm, pandas, numpy, shap, transformers, torch
- [x] Set up Git repository with .gitignore

---

## 🟡 PHASE 2: Backend Core (FastAPI + Database)

### Database
- [ ] Design PostgreSQL schema:
  - [ ] users table (id, email, password_hash, role, created_at, is_anonymous)
  - [ ] sessions table (id, user_id, started_at, ended_at, is_complete)
  - [ ] screening_responses table (id, session_id, instrument, item_number, response_value, timestamp)
  - [ ] 
isk_scores table (id, session_id, phq9_score, gad7_score, pss10_score, composite_risk_level, ml_risk_label, shap_values_json)
  - [ ] crisis_events table (id, session_id, trigger_type, timestamp, response_sent)
- [ ] Write Alembic migrations for all tables
- [ ] Test database connection and CRUD operations

### Authentication
- [ ] Implement user registration endpoint (POST /auth/register)
- [ ] Implement user login endpoint (POST /auth/login) with JWT token
- [ ] Implement anonymous session endpoint (POST /auth/anonymous)
- [ ] Implement JWT middleware for protected routes
- [ ] Add role-based access (student / counselor / admin)

### Session and Conversation API
- [ ] POST /sessions/start — start a new screening session
- [ ] GET /sessions/{id} — get session state
- [ ] POST /sessions/{id}/message — send a message, get chatbot reply
- [ ] POST /sessions/{id}/complete — finalize session and trigger scoring
- [ ] GET /sessions/{id}/results — get risk scores and recommendations

---

## 🟢 PHASE 3: Screening Engine (Deterministic Scoring)

- [ ] Implement PHQ9Scorer class
  - [ ] 9 items, scored 0–3
  - [ ] Total score 0–27
  - [ ] Severity classification: Minimal (0–4), Mild (5–9), Moderate (10–14), Mod-Severe (15–19), Severe (20–27)
- [ ] Implement GAD7Scorer class
  - [ ] 7 items, scored 0–3
  - [ ] Total score 0–21
  - [ ] Severity classification: Minimal (0–4), Mild (5–9), Moderate (10–14), Severe (15–21)
- [ ] Implement PSS10Scorer class
  - [ ] 10 items (4 items are reverse scored: Q4, Q5, Q7, Q8)
  - [ ] Total score 0–40
  - [ ] Severity: Low (0–13), Moderate (14–26), High (27–40)
- [ ] Implement CompositeRiskCalculator — combines all 3 scores into Low/Moderate/High
- [ ] Write unit tests for all scoring classes (edge cases: all-zero, all-max, mixed)
- [ ] Validate against published clinical cutoff tables

---

## 🔵 PHASE 4: LLM Chatbot Integration

- [ ] Design and write the system prompt (empathic persona, guardrails, non-diagnostic clause)
- [ ] Set up LangChain with chosen LLM provider (OpenAI or Groq)
- [ ] Implement conversation state machine with LangGraph:
  - [ ] State: greeting → consent → background → phq9_screening → gad7_screening → pss_screening → 
esults
  - [ ] State transitions triggered by questionnaire completion
- [ ] Implement questionnaire injection into dialogue flow (conversational interleaving)
- [ ] Store conversation history in memory + sync to DB
- [ ] Implement response streaming (Server-Sent Events or WebSocket)
- [ ] Test full conversation flow end-to-end

---

## 🟣 PHASE 5: Crisis Detection Module

- [ ] Define crisis keyword dictionary (English + common Hindi phrases)
  - [ ] Suicidal ideation: "want to die", "kill myself", "end my life", "no reason to live"
  - [ ] Self-harm: "hurt myself", "cut myself"
  - [ ] Hopelessness: "no hope", "nothing matters anymore" (as secondary signals)
- [ ] Implement KeywordCrisisDetector class
  - [ ] Regex-based matching (case-insensitive, handles typos with fuzzy matching optional)
  - [ ] Returns: is_crisis: bool, trigger_type: str, confidence: float
- [ ] Implement CrisisResponder class
  - [ ] Hard-coded crisis response message template
  - [ ] Includes: iCall (9152987821), Vandrevala Foundation (1860-2662-345), campus contact placeholder
  - [ ] Logs crisis event to crisis_events table
- [ ] Hook crisis detector into message processing pipeline (runs BEFORE LLM)
- [ ] Write unit tests for crisis detection (true positives, false positives)

---

## ⚫ PHASE 6: ML Risk Classification Pipeline

### Data Preparation
- [ ] Collect or generate dataset
  - [ ] Synthetic data: Generate N=500+ samples from published PHQ-9/GAD-7/PSS-10 distributions
  - [ ] Kaggle datasets: Download and clean mental health survey data
  - [ ] Label composite risk (Low/Moderate/High) from clinical cutoffs
- [ ] EDA notebook: distribution plots, class balance, correlation heatmap
- [ ] Handle class imbalance (SMOTE or class_weight='balanced')

### Feature Engineering
- [ ] Build feature extraction pipeline:
  - [ ] 26 individual questionnaire item scores
  - [ ] 3 subscale totals
  - [ ] Time-of-day (morning/afternoon/evening/night)
  - [ ] Is returning user (binary)
  - [ ] Session number
- [ ] StandardScaler / MinMaxScaler for continuous features
- [ ] LabelEncoder / OrdinalEncoder for categorical features

### Model Training
- [ ] Train Logistic Regression baseline
- [ ] Train Random Forest
- [ ] Train XGBoost (hyperparameter tuned with Optuna or GridSearchCV)
- [ ] Train LightGBM
- [ ] Train SVM (RBF kernel)

### Evaluation
- [ ] Stratified 5-fold cross-validation for all models
- [ ] Compute: Accuracy, Macro-F1, Precision, Recall, Confusion Matrix, AUC-ROC
- [ ] Compare models in comparison table
- [ ] SHAP analysis on best model (XGBoost)
  - [ ] SHAP summary plot
  - [ ] SHAP force plot for individual predictions
  - [ ] SHAP feature importance bar chart
- [ ] Save best model as .pkl artifact

### API Integration
- [ ] Create ML inference endpoint: POST /ml/predict
- [ ] Load saved model in FastAPI startup
- [ ] Return: 
isk_label, confidence, shap_values

---

## 🟤 PHASE 7: Frontend — Chat Interface (React)

### Pages
- [ ] **Home Page** — landing page with "Start Screening" CTA, disclaimer visible
- [ ] **Consent Page / Modal** — full informed consent text, accept button
- [ ] **Chat Page** — main chat interface
- [ ] **Results Page** — risk level display, coping suggestions, counselor link

### Components
- [ ] ChatWindow — renders message history
- [ ] MessageBubble — student/bot message with timestamps
- [ ] ConsentModal — cannot be dismissed without accepting
- [ ] QuestionCard — for PHQ/GAD scale questions with Likert scale buttons
- [ ] RiskResultCard — displays risk level (Low/Moderate/High with color)
- [ ] CopingSuggestionCard — personalized coping content
- [ ] CrisisAlert — banner/overlay that appears when crisis detected
- [ ] DisclaimerBanner — persistent at top of chat window

### Functionality
- [ ] Connect to FastAPI backend via Axios
- [ ] Implement real-time message streaming (SSE or WebSocket)
- [ ] Store session token in localStorage
- [ ] Handle anonymous vs authenticated user flows
- [ ] Responsive design (mobile + desktop)

---

## 🏁 PHASE 8: Review 1 Finalization

- [ ] Run full end-to-end test: login → consent → full screening → results
- [ ] Verify scoring accuracy against manual calculation
- [ ] Verify crisis detection triggers and responds correctly
- [ ] Verify ML model integration returns predictions
- [ ] Write and generate API docs (FastAPI /docs auto-generated)
- [ ] Write README.md with:
  - [ ] Project overview
  - [ ] Setup instructions (Docker Compose)
  - [ ] Architecture summary
  - [ ] How to run
- [ ] Prepare demo script for Review 1 presentation
- [ ] Record demo video (optional but recommended)

---

## 📅 LATER PHASES (Post Review 1)

### Review 2 Tasks
- [ ] Counselor Dashboard (React admin panel)
  - [ ] Student risk queue (triage view)
  - [ ] Individual student longitudinal charts
  - [ ] Population heatmaps and analytics
  - [ ] SHAP explainability panel
  - [ ] Crisis alert notifications
- [ ] Advanced ML: LightGBM final model, MentalBERT NLP features
- [ ] RAG-based psychoeducation engine (LangChain + pgvector)
- [ ] ML crisis classifier (RoBERTa fine-tuned)
- [ ] PII Anonymization (Microsoft Presidio integration)
- [ ] Longitudinal tracking: track student progress over multiple sessions
- [ ] Security hardening: rate limiting, input sanitization, audit logs
- [ ] Deployment: Docker → cloud (GCP / AWS)
- [ ] Final documentation and project defense preparation

---

## 📊 Review 1 Progress Tracker

| Module | Status | % Done |
|---|---|---|
| Phase 0: Research + Planning | [ ] | 0% |
| Phase 1: Project Setup | [x] | 100% |
| Phase 2: Backend Core | [ ] | 0% |
| Phase 3: Screening Engine | [ ] | 0% |
| Phase 4: LLM Chatbot | [ ] | 0% |
| Phase 5: Crisis Detection | [ ] | 0% |
| Phase 6: ML Pipeline | [ ] | 0% |
| Phase 7: Frontend | [ ] | 0% |
| Phase 8: Review 1 Polish | [ ] | 0% |
| **Overall** | **[/]** | **~15%** |
