# MindEase — ML-Assisted Mental Health Screening Chatbot
## Project Feature Specifications & Future Roadmap

**Project Name:** MindEase (Mental Health Screening for University Students)  
**Document Version:** 1.0 (Review 1 Baseline)  
**Date:** August 28, 2026  
**Status:** Review 1 Target Complete (100%)  

---

## 📌 Executive Summary
MindEase is a clinical-grade, AI-assisted mental health screening platform designed for university students. It combines **validated psychometric instruments** (PHQ-9, GAD-7, PSS-10), a **hybrid conversational chatbot** (LLM + deterministic delivery), a **pre-LLM bilingual crisis safety guardrail**, and an **XGBoost Machine Learning model with SHAP explainability** trained on 39,648 real human participant responses.

---

# 🚀 Part 1: Implemented Features (Review 1 — 100% Complete)

### 1. Deterministic Clinical Scoring Engine
* **PHQ-9 (Patient Health Questionnaire - 9):**
  * Evaluates depression severity over the preceding 2 weeks.
  * 9 clinical items scored on a 0–3 Likert scale (Total range: 0–27).
  * Standard clinical cutoffs: *Minimal (0–4), Mild (5–9), Moderate (10–14), Moderately Severe (15–19), Severe (20–27)*.
* **GAD-7 (Generalized Anxiety Disorder - 7):**
  * Evaluates anxiety symptoms over the preceding 2 weeks.
  * 7 clinical items scored on a 0–3 Likert scale (Total range: 0–21).
  * Standard clinical cutoffs: *Minimal (0–4), Mild (5–9), Moderate (10–14), Severe (15–21)*.
* **PSS-10 (Perceived Stress Scale - 10):**
  * Evaluates chronic stress and coping ability over the past month.
  * 10 items scored 0–4 (Total range: 0–40).
  * Reverse scoring mathematically enforced on positively phrased items (Q4, Q5, Q7, Q8).
  * Clinical cutoffs: *Low Stress (0–13), Moderate Stress (14–26), High Stress (27–40)*.
* **Composite Risk Calculator:**
  * Clinically combines subscale scores to produce an overall triage level (*Low, Moderate, High Risk*).

---

### 2. Conversational Chatbot Engine (Hybrid Architecture)
* **Empathic Conversational Layer (Groq LLM):**
  * Powered by `openai/gpt-oss-20b` via Groq.
  * Manages greeting, informed consent, student background check-in, and personalized coping advice with warm, empathetic language.
* **Authoritative Psychometric Delivery (Zero Hallucination):**
  * During questionnaire stages (`phq9`, `gad7`, `pss10`), the bot delivers exact, standardized question text and interactive Likert options directly from clinical definitions.
* **Dialogue State Machine:**
  * Structured flow: `greeting` → `consent` → `background` → `phq9` → `gad7` → `pss10` → `results`.
* **Real-Time Streaming & Persistence:**
  * Server-Sent Events (`POST /api/v1/chat/stream`) for real-time typewriter UI effect.
  * Full session conversation history persisted in PostgreSQL `chat_messages` table.

---

### 3. Pre-LLM Crisis Interception & Safety Guardrails
* **Zero-Latency Synchronous Interception:**
  * Keyword and regex pattern detection executes *before* any prompt reaches the LLM, eliminating AI hallucination risks during emergencies.
* **Bilingual Distress Detection:**
  * English triggers: suicidal ideation, self-harm, severe hopelessness.
  * Hinglish triggers: *"mar jana"*, *"khudkushi"*, *"khatam karna"*, *"jeene ka mann nahi"*, *"apni jaan lena"*.
* **Safe-Idiom False-Positive Filter:**
  * Contextually filters out colloquial expressions (e.g., *"this exam is killing me"* is not flagged as a crisis).
* **Immediate Emergency Action Card:**
  * Displays verified crisis helplines: **iCall (`9152987821`)**, **Vandrevala Foundation (`1860-2662-345`)**, and **National Emergency (`112`)**.

---

### 4. Machine Learning Risk Classifier & Explainable AI (SHAP)
* **Real Dataset Grounding:**
  * Trained on **39,648 real human participant responses** from the OpenPsychometrics DASS-42 Survey.
* **39 Engineered Clinical Features:**
  * 26 individual item responses.
  * 3 subscale totals (`phq9_total`, `gad7_total`, `pss10_total`).
  * Peak symptom distress indicators (`phq9_max_item`, `gad7_max_item`).
  * Severe symptom counts ($\ge 2$) and response consistency variance.
  * PHQ-9 Item 9 self-harm marker isolation.
* **Model Benchmark & Selection (5-Fold Stratified Cross-Validation):**
  * *Logistic Regression:* 87.2% Accuracy | F1: 0.869
  * *Random Forest:* 90.8% Accuracy | F1: 0.903
  * *XGBoost Classifier:* **91.1% Accuracy | F1: 0.906 (Best Deployed Model)**
* **Explainable AI (SHAP):**
  * Computes TreeExplainer SHAP values to explain the top symptom contributors for each triage classification.
* **Dynamic Per-Session Confidence:**
  * Computes probability-based confidence ($P(\text{Risk})$) tailored specifically to the student's individual session answers.

---

### 5. Full-Stack Web Application
* **Frontend (React + TypeScript + Vite + Tailwind CSS):**
  * Clean, student-friendly interface.
  * Informed Consent Modal, Interactive Chat with quick-select Likert buttons, and Comprehensive Results Dashboard.
  * 3-panel clinical score breakdown, XGBoost confidence badge, SHAP explainability tags, customized self-care strategies, and campus emergency links.
* **Backend Core (FastAPI + PostgreSQL 16 + SQLAlchemy):**
  * Asynchronous ORM with native PostgreSQL 16.
  * JWT Authentication supporting both registered user profiles and anonymous guest sessions.
  * Automated test suite: 18/18 quick smoke tests, 12/12 E2E endpoint checks, and 14/14 crisis detector tests passing (100%).

---

# 🔮 Part 2: Future Roadmap (Features to be Implemented)

### Phase 9: Counselor / Clinical Admin Portal (Review 2 Target)
* **Student Risk Triage Queue:** Real-time dashboard for campus counselors sorting students by risk priority (*High Risk flagged for immediate attention*).
* **Longitudinal Trend Visualizations:** Interactive historical charts displaying a student’s score changes over multiple screenings across the semester.
* **Campus-Wide Anonymized Analytics:** Department-level and university-wide mental wellness heatmaps to identify high-stress academic periods.
* **Clinical Report Export:** Automated PDF summary generation for clinical handoff and referrals.

---

### Phase 10: RAG-Powered Psychoeducation Engine (Review 2 Target)
* **Clinical Vector Knowledge Base:** Integration of **pgvector** or ChromaDB indexing evidence-based Cognitive Behavioral Therapy (CBT) exercises, mindfulness guides, and university support services.
* **Retrieval-Augmented Generation (RAG):** Dynamically retrieves and presents relevant psychoeducational exercises tailored to the student's primary distress area during conversations.

---

### Phase 11: Deep Learning NLP Distress Classifier (Review 2 / 3 Target)
* **MentalBERT / RoBERTa Fine-Tuning:** Transformer-based sentiment and emotion classification trained on clinical text datasets to evaluate free-text student messages alongside structured questionnaire scores.
* **Behavioral Latency Analysis:** Integration of item response latency (elapsed answering time) as an auxiliary predictive feature.

---

### Phase 12: Privacy Hardening & Data Anonymization (Review 3 Target)
* **Automated PII Scrubbing:** Integration of **Microsoft Presidio** to detect and anonymize Personally Identifiable Information (names, student IDs, phone numbers) before saving text to database logs.
* **HIPAA/GDPR Compliance Tools:** Automated student data export and "Right to be Forgotten" account purging mechanisms.

---

### Phase 13: Multi-Session Longitudinal Tracking (Review 3 Target)
* **Student Progress Tracking:** Calculates symptom recovery deltas across multiple sessions.
* **Automated Follow-Up Reminders:** Optional opt-in check-in reminders (e.g., 2-week or 1-month follow-up screenings).

---

### Phase 14: Production Cloud Deployment & DevOps (Final Phase)
* **Cloud Infrastructure:** Deployment to AWS (ECS / Fargate + RDS PostgreSQL) or GCP (Cloud Run + Cloud SQL).
* **Automated CI/CD:** GitHub Actions workflows for automated linting, test execution, and deployment.
* **Production Security:** API rate limiting, Web Application Firewall (WAF), strict CORS, and SSL/TLS termination.

---

# 📊 Part 3: Technical Specifications & Verification Table

| Component | Current Technology / Specification |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | Python 3.14, FastAPI, Uvicorn, Pydantic v2 |
| **Database** | PostgreSQL 16 (Native), SQLAlchemy Async ORM, asyncpg |
| **LLM Provider** | Groq API (`openai/gpt-oss-20b`, temperature=0.5) |
| **ML Classifier** | XGBoost Classifier (200 estimators, max_depth=6, learning_rate=0.1) |
| **ML Training Dataset** | OpenPsychometrics DASS-42 Dataset (**39,648 real participants**) |
| **Cross-Validation Accuracy** | **91.1% 5-Fold Stratified CV Accuracy (F1-Macro: 0.906)** |
| **Explainability** | SHAP (SHapley Additive exPlanations) TreeExplainer |
| **Safety Interceptor** | Pre-LLM Regex & Keyword Engine (Bilingual: English + Hinglish) |
| **Authentication** | JWT (HS256) with Passlib bcrypt password hashing |
| **Verification Status** | **18/18 Quick Smoke Checks Pass (100%)** |

---

*Document generated automatically for MindEase Project Review Documentation.*
