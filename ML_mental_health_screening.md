# ML‑Assisted Mental Health Screening Chatbot for University Students

## 1. Project Overview

University students commonly experience high levels of stress, anxiety, and depression due to academic pressure, personal and social challenges, and transitional life phases. [web:47][web:60] Campus counseling centers often face limited resources and increasing demand, which can delay support and leave many students without timely assistance. [web:41][web:56]  

AI‑based mental health chatbots provide scalable, anonymous, and low‑cost support and are increasingly used as a supplementary tool for young people. [web:43][web:44][web:60] Systematic reviews show that such chatbots can modestly reduce psychological distress and improve mental health literacy when integrated with existing services. [web:52][web:53][web:57][web:60]  

This project proposes an **ML‑assisted mental health screening chatbot** tailored for university students, designed explicitly to support—rather than replace—the campus counseling/consultation department.

---

## 2. Problem Statement

Even when counseling services are available, many students:

- Delay or avoid seeking help due to stigma, lack of awareness, or scheduling barriers. [web:56][web:60]  
- Reach counselling sessions without prior structured assessment, making initial evaluation time‑consuming and inconsistent. [web:41][web:55]  

There is a need for an accessible, anonymous, and standardized pre‑screening tool that:

- Helps students reflect on their mental health and receive basic guidance.  
- Supports counsellors by providing summarized, standardized information on distress levels and presenting problems before or between sessions.

---

## 3. Aim

To design and implement an **ML‑assisted conversational chatbot** for university students that:

- Conducts brief, validated mental health screening.  
- Estimates psychological distress risk levels (e.g., low, moderate, high).  
- Provides psychoeducational content and self‑help suggestions.  
- Encourages timely use of the university’s counseling/consultation services.

---

## 4. Objectives

1. **Screening Integration**  
   - Embed validated mental health questionnaires (e.g., for depression, anxiety, stress) into a conversational chatbot flow suitable for university students. [web:43][web:55]  

2. **Risk Prediction (ML)**  
   - Build and evaluate machine learning models that classify students’ distress/risk level based on questionnaire responses and simple contextual features. [web:52][web:53][web:60]  

3. **Conversational Support**  
   - Design a chatbot interface (web or mobile) that delivers screening questions, interprets results in simple language, and offers basic coping suggestions and resource links. [web:44][web:47]  

4. **Counsellor Assistance**  
   - Develop an optional counselor dashboard that displays anonymized or consent‑based screening summaries to help with triage and follow‑up planning. [web:47][web:50]  

5. **Ethics, Safety, and Privacy**  
   - Implement clear disclaimers, crisis‑response rules (e.g., for suicidal ideation), and data privacy measures aligned with ethical guidelines for digital mental health tools. [web:46][web:55][web:57][web:59][web:60]  

---

## 5. Scope

- **Target Users:** University students (e.g., ages 18–25) with subclinical to moderate distress; the tool is **not** a diagnostic system for severe psychiatric disorders. [web:47]  
- **Setting:** Campus context—pre‑screening before/after counselling, or self‑use via link/QR code.  
- **Function:** Screening, psychoeducation, and nudging toward professional help; no medication recommendations or formal diagnoses. [web:55][web:59]  
- **Duration:** 4 months, focusing on prototype development and technical evaluation, not full clinical deployment.

---

## 6. Related Work (Summary)

### 6.1 Mental Health Chatbots for Youth and Students

Studies show that chatbot‑based interventions can reduce depression, anxiety, and overall psychological distress in adolescents and young adults, with small to moderate effect sizes. [web:44][web:52][web:53][web:56][web:60] Several interventions target help‑seeking barriers and mental health literacy, highlighting chatbots as a scalable supplement to traditional care. [web:56][web:59][web:60]  

Pilot work with university students suggests that integrating an AI chatbot as adjunct support between group therapy sessions is feasible, acceptable, and shows preliminary improvements in anxiety and well‑being. [web:47][web:50][web:58]  

### 6.2 CBT‑Based and Psychoeducational Chatbots

CBT‑based chatbots commonly offer cognitive restructuring, behavioral activation, and mindfulness strategies, implemented through text dialogues and self‑monitoring. [web:55][web:46] Evidence indicates short‑term reductions in depressive and anxiety symptoms, particularly over 4–8 weeks. [web:55][web:52]  

### 6.3 Design and Ethical Considerations

Systematic reviews highlight key design features (dialogue systems, reminders, personalization) and emphasize safety protocols, privacy, and crisis management. [web:46][web:57][web:59] Limitations include variable clinical evidence, lack of long‑term data, and the need for rigorous evaluation frameworks, especially for generative AI systems. [web:52][web:57][web:59]  

---

## 7. Methodology

### 7.1 System Architecture

**Core Components:**

- **Chatbot Frontend:**  
  - Web or mobile‑friendly interface for text‑based interaction with students.  

- **Conversation & Screening Engine:**  
  - Dialogue flow handling consent, background questions, and validated screening questionnaires embedded as conversational items. [web:43][web:55]  

- **ML Risk Scoring Module:**  
  - Input: questionnaire responses and optional metadata (e.g., usage time, repeat visits).  
  - Output: distress risk level (low, moderate, high) and possibly subscores (stress, mood, anxiety). [web:52][web:53][web:60]  

- **Counsellor Dashboard (Prototype):**  
  - Aggregated statistics and, with consent, individual summaries to assist triage and follow‑up planning. [web:47][web:50]  

- **Database & Security Layer:**  
  - Secure storage of responses and model outputs with anonymization/pseudonymization, role‑based access control, and data retention policies. [web:59][web:60]  

### 7.2 Data and Instruments

- **Screening Instruments:**  
  - Short forms of validated questionnaires (e.g., PHQ‑9, GAD‑7, stress scale), adapted into conversational prompts while maintaining scoring integrity. [web:43][web:55]  

- **Dataset for ML:**  
  - Collect responses from volunteer students via the chatbot or an integrated online form.  
  - Optionally augment with synthetic data reflecting plausible distributions based on published studies, clearly documented in the methodology. [web:52][web:53][web:60]  

### 7.3 Machine Learning Approach

- **Task:**  
  - Multi‑class classification (low / moderate / high distress) based on questionnaire scores and features.  

- **Features:**  
  - Individual item scores, total scores per scale, and simple contextual features (e.g., time of usage, repeated usage patterns).  

- **Models:**  
  - Logistic Regression, Random Forest, Gradient Boosting, or similar interpretable models for tabular data. [web:39]  

- **Evaluation Metrics:**  
  - Accuracy, precision, recall, F1‑score per class; confusion matrix analysis.  
  - Cross‑validation if sample size is limited, with emphasis on proof‑of‑concept rather than definitive clinical performance. [web:52][web:53]  

### 7.4 Chatbot Design

- **Tone & Language:**  
  - Empathic, non‑judgmental, and simple English suitable for diverse student backgrounds; potential future extension to Indian languages using available datasets. [web:36]  

- **Conversation Flow:**  
  - Greeting, explanation, and consent.  
  - Background questions (optional).  
  - Screening questions, one by one.  
  - Simple, non‑diagnostic feedback (e.g., “Your responses suggest moderate stress.”).  
  - Self‑help suggestions and links to university counselling services (booking, location, contact). [web:47][web:50]  

- **Safety Protocols:**  
  - For indications of severe symptoms or suicidal ideation, display high‑priority messages encouraging immediate human help, including helpline numbers and campus emergency contacts. [web:57][web:59][web:60]  

---

## 8. Ethical, Privacy, and Psychological Considerations

- **Non‑Replacement of Professionals:**  
  - The chatbot is explicitly framed as a **support and screening tool**, not a diagnostic or therapeutic replacement for mental health professionals. [web:55][web:59]  

- **Informed Consent:**  
  - Clear information on purpose, data usage, limitations, and crisis procedures before any screening.  

- **Confidentiality and Security:**  
  - Secure storage, limited access, removal of personally identifiable information wherever possible. [web:59][web:60]  

- **Psychological Safety:**  
  - Consultation with psychology/counseling faculty to review questionnaire selection, wording, feedback, and crisis response design. [web:41][web:49][web:48]  

---

## 9. Expected Outcomes

- A functional chatbot prototype capable of conducting basic mental health screening and delivering supportive messages to university students.  
- A trained ML model capable of classifying distress levels with reasonable performance on collected data. [web:52][web:53][web:57][web:60]  
- Demonstration of how such a tool can support campus counseling by streamlining pre‑screening, enhancing between‑session support, and promoting earlier help‑seeking. [web:47][web:50][web:58]  

---

## 10. Limitations

- Single‑institution, relatively small sample limiting generalizability.  
- Prototype evaluation focuses on technical and usability metrics rather than long‑term clinical outcomes. [web:55][web:57][web:59]  
- The chatbot is not designed to handle complex multi‑diagnostic or emergency cases; it primarily supports screening and guidance. [web:55][web:59][web:60]  

---

## 11. Proposed 4‑Month Timeline

- **Month 1:**  
  - Detailed literature review.  
  - Finalize questionnaires and screening logic.  
  - Design architecture and conversation flow.  

- **Month 2:**  
  - Implement chatbot frontend and backend.  
  - Set up database and initial ML pipeline scaffolding.  

- **Month 3:**  
  - Collect pilot data from students.  
  - Train and evaluate ML models; refine conversation and feedback based on user and faculty input.  

- **Month 4:**  
  - Integrate risk scoring with chatbot.  
  - Implement basic counselor dashboard (optional).  
  - Final testing, documentation, and project defense preparation.

---

## 12. Key References (Must Read)

1. Chatbot‑Delivered Interventions for Improving Mental Health Among Young People: Systematic Review and Meta‑Analysis. [web:60]  
2. The Impact of Chatbots on Adolescent Mental Health (comprehensive review). [web:56]  
3. Evidence for the Use of an Adolescent Mental Health Chatbot (feasibility and acceptability). [web:44]  
4. Breaking Barriers in Student Mental Health Care With AI‑Enhanced Support (LLM‑based adjunct chatbot for university students). [web:47]  
5. AI‑Enhanced Chatbots for Psychological Support in University Settings (Kolkata‑based study). [web:50]  
6. Systematic Review and Meta‑Analysis of Chatbots in Managing Depressive and Anxiety Symptoms. [web:57]  
7. Effectiveness of AI Chatbot Interventions for Mental Distress and Health Behaviors Among Adolescents and Young Adults. [web:53]  
8. Generative AI Mental Health Chatbots: Evidence and Safety Considerations (narrative/systematic reviews). [web:52][web:59]  
9. Clinical Efficacy and Mechanisms of CBT‑Based AI Chatbots for Depression and Anxiety. [web:55]  
10. Mental Health Chatbots: Trends, Design, and Ethical Considerations (systematic review). [web:46]  
11. MindEase or similar AI‑powered digital mental health systems for students (Indian context). [web:41][web:49][web:48]  

---

### Note

You can adapt this README into:

- A formal **synopsis** (by adding university name, department, guide, and student details).  
- A **GitHub README** (by adding sections for installation, tech stack, and usage once you start coding).
