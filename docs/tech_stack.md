# MindEase Technology Stack

## Overview

This document details every technology decision in the MindEase Mental Health Screening Chatbot, with rationale, alternatives considered, and integration notes.

---

## Architecture Pattern

**Chosen**: Three-tier architecture (Frontend SPA → REST API → PostgreSQL)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Monorepo, separated frontend/backend | Clear separation of concerns; easy to containerize independently |
| API Style | REST (JSON) | Industry standard, simpler than GraphQL for this use case; broad tooling support |
| Deployment | Docker Compose (dev) → containers (prod) | Consistent environments; easy to scale horizontally |

---

## Frontend Stack

### Core Framework: React 18 + TypeScript

| Property | Value |
|----------|-------|
| **Technology** | React 18 + TypeScript 5.x |
| **Version** | React 18.3+ |
| **Why React** | Largest ecosystem; component model ideal for chatbot UI; team familiarity |
| **Why TypeScript** | Type safety critical for medical/health data; better IDE support; fewer runtime bugs |

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Vue 3 | Smaller ecosystem; fewer UI component libraries |
| Angular | Too opinionated; overkill for this project size |
| Svelte | Smaller community; fewer mental-health UI templates |
| Plain JavaScript | No type safety; error-prone for complex state management |

---

### Build Tool: Vite

| Property | Value |
|----------|-------|
| **Technology** | Vite 5.x |
| **Why Vite** | 10–100x faster HMR than CRA/Webpack; native ESM; minimal config |
| **Config** | TypeScript, React plugin, path aliases |

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Create React App | Deprecated; slow build times; limited config |
| Webpack | Complex configuration; slower dev server |
| Parcel | Less TypeScript support; fewer plugins |

---

### Styling: Tailwind CSS + shadcn/ui

| Property | Value |
|----------|-------|
| **CSS Framework** | Tailwind CSS 3.x |
| **Component Library** | shadcn/ui (Radix UI primitives) |
| **Why Tailwind** | Utility-first enables rapid, consistent UI; small bundle size with purging |
| **Why shadcn/ui** | Accessible (WCAG 2.1) components critical for mental health app; customizable; no external dependency lock-in |

**Accessibility Note**: Mental health applications must meet WCAG 2.1 AA standards. Radix UI primitives (powering shadcn/ui) handle ARIA roles, keyboard navigation, and focus management automatically.

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Material UI | Heavy bundle; less customizable design tokens |
| Chakra UI | More opinionated; less Tailwind synergy |
| Bootstrap | Dated aesthetics; less flexible for custom chatbot UI |
| CSS Modules | Too verbose for rapid iteration |

---

### State Management: React Context + TanStack Query

| Property | Value |
|----------|-------|
| **Global State** | React Context + useReducer |
| **Server State** | TanStack Query (React Query) v5 |
| **Why Context** | Auth state and session state are simple enough; no need for Redux |
| **Why TanStack Query** | Automatic caching, refetching, and loading states for API calls; reduces boilerplate |

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Redux Toolkit | Overkill for this app's state complexity |
| Zustand | Good option but TanStack Query covers most server-state needs |
| SWR | TanStack Query is more feature-rich for this use case |

---

### Routing: React Router v6

| Property | Value |
|----------|-------|
| **Technology** | React Router v6 |
| **Why** | Industry standard; file-based routing option; nested routes for dashboard |

---

## Backend Stack

### API Framework: FastAPI + Python

| Property | Value |
|----------|-------|
| **Framework** | FastAPI 0.110+ |
| **Runtime** | Python 3.11+ |
| **ASGI Server** | Uvicorn (with Gunicorn in prod) |
| **Why FastAPI** | Automatic OpenAPI/Swagger docs; native async support; Pydantic validation built-in; fastest Python web framework |
| **Why Python** | Best ML/AI ecosystem (scikit-learn, LangChain, HuggingFace) |

**Performance**: FastAPI benchmarks at ~70,000 req/s (comparable to Node.js), far exceeding this application's needs.

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Flask | Synchronous by default; no built-in validation; less auto-documentation |
| Django REST Framework | Too heavy; ORM coupling; slower for pure API service |
| Node.js / Express | Weaker ML ecosystem; would require separate Python microservice anyway |
| Go / Gin | Excellent performance but poor ML library support |

---

### Data Validation: Pydantic v2

| Property | Value |
|----------|-------|
| **Technology** | Pydantic v2 |
| **Why** | Native FastAPI integration; 5-17x faster than v1; strict type validation for health data; automatic JSON serialization |

---

### Authentication: JWT + bcrypt

| Property | Value |
|----------|-------|
| **Token Standard** | JWT (JSON Web Tokens) via `python-jose` |
| **Password Hashing** | bcrypt via `passlib[bcrypt]` |
| **Token Types** | Short-lived Access Token (15 min) + Refresh Token (7 days) |
| **Why JWT** | Stateless; no session storage needed; works well with React SPA |
| **Why bcrypt** | Industry standard for password hashing; adaptive cost factor; proven security |

**Security Details**:
- Access tokens: 15-minute expiry, stored in memory (not localStorage)
- Refresh tokens: 7-day expiry, stored in HTTP-only cookies
- bcrypt cost factor: 12 (adjustable as hardware improves)
- All tokens include user ID, expiry, and token type claims

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Session-based auth | Requires server-side session storage; harder to scale |
| OAuth2 only | Adds complexity; no social login needed for MVP |
| argon2 | More modern but bcrypt has wider library support in Python ecosystem |
| SHA-256 | Not suitable for password hashing (too fast; vulnerable to brute force) |

---

## Database Stack

### Primary Database: PostgreSQL 15

| Property | Value |
|----------|-------|
| **Database** | PostgreSQL 15+ |
| **Why PostgreSQL** | ACID compliance critical for health data; JSON support; pgvector extension; excellent async driver (asyncpg) |
| **Extensions** | `pgvector` for embedding storage |

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| MySQL | Weaker JSON support; no pgvector equivalent; less advanced full-text search |
| MongoDB | Eventual consistency problematic for health records; joins harder |
| SQLite | Not suitable for production multi-user application |
| Supabase (hosted PG) | Good option for later; MVP prefers self-hosted control |

---

### Vector Extension: pgvector

| Property | Value |
|----------|-------|
| **Technology** | pgvector extension for PostgreSQL |
| **Use Case** | Store conversation embeddings for semantic search + future RAG features |
| **Embedding Model** | Groq / OpenAI embeddings (configurable) |
| **Dimensions** | 1536 (OpenAI ada-002) or 4096 (LLaMA embeddings) |
| **Why** | Keeps vector search in same DB as relational data; no separate vector DB needed for MVP |

**Future Consideration**: If semantic search volume grows, migrate to dedicated Pinecone or Weaviate instance.

---

### ORM: SQLAlchemy 2.0 Async

| Property | Value |
|----------|-------|
| **Technology** | SQLAlchemy 2.0 |
| **Mode** | Async (with `asyncpg` driver) |
| **Migrations** | Alembic |
| **Why SQLAlchemy** | Most mature Python ORM; excellent async support in v2; full control over SQL when needed |
| **Why asyncpg** | Fastest async PostgreSQL driver for Python; binary protocol |

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Tortoise ORM | Less mature; smaller community |
| Databases (encode) | Lower-level; more boilerplate |
| Raw SQL (psycopg3) | Too much boilerplate for complex queries |
| Prisma (Python) | Alpha stage for Python; not production-ready |

---

## AI / ML Stack

### LLM Orchestration: LangChain + Groq

| Property | Value |
|----------|-------|
| **Orchestration** | LangChain 0.2+ |
| **LLM Provider** | Groq API |
| **Models** | LLaMA 3 70B / Mixtral 8x7B |
| **Why LangChain** | Standardized chain/prompt management; easy provider switching; memory management for conversation context |
| **Why Groq** | Fastest LLM inference API (LPU hardware); free tier generous; supports LLaMA 3 and Mixtral; very low latency |

**Latency Benchmark**: Groq achieves ~500 tokens/second vs ~50 tokens/second for typical cloud LLMs, critical for real-time chatbot feel.

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| OpenAI GPT-4 | Cost; rate limits; data privacy concerns for health app |
| Anthropic Claude | Higher cost; no self-hosting option |
| Ollama (local) | Insufficient GPU in development; deployment complexity |
| Google Gemini API | Less LangChain integration maturity at project start |
| LlamaIndex | Better for RAG/document retrieval; LangChain better for conversation chains |

---

### ML Model: scikit-learn Random Forest

| Property | Value |
|----------|-------|
| **Library** | scikit-learn 1.4+ |
| **Model** | Random Forest Classifier |
| **Target** | Overall risk level (low / moderate / high / very_high) |
| **Features** | PHQ-9 score, GAD-7 score, PSS-10 score, item-level scores, demographics |
| **Why Random Forest** | Handles mixed feature types well; robust to outliers; interpretable feature importance; no feature scaling required; proven in clinical decision support literature |

**Model Details**:
- Estimators: 100–500 trees
- Max depth: tuned via cross-validation
- Class weights: balanced (handles imbalanced mental health data)
- Serialization: `joblib` for model persistence

**Alternatives Considered**:

| Alternative | Reason Not Chosen |
|-------------|------------------|
| Logistic Regression | Too simple; may underfit non-linear relationships |
| XGBoost / LightGBM | Marginally better performance but less interpretable; more complex to tune |
| Neural Network (MLP) | Overkill for tabular data with 26 features; harder to explain to clinicians |
| SVM | Slower training; less interpretable; poor with imbalanced classes |
| Rule-based system | Cannot learn from data; inflexible to new patterns |

---

## Infrastructure & DevOps

### Containerization: Docker + Docker Compose

| Property | Value |
|----------|-------|
| **Technology** | Docker 24+ + Docker Compose v2 |
| **Why Docker** | Consistent dev/prod environments; easy dependency isolation |
| **Services** | `frontend`, `backend`, `db` (PostgreSQL), `nginx` |

### CI/CD: GitHub Actions

| Property | Value |
|----------|-------|
| **Technology** | GitHub Actions |
| **Pipeline** | Lint → Test → Build → Push image → Deploy |
| **Why** | Free for public repos; tightly integrated with GitHub; large action marketplace |

### Reverse Proxy: Nginx

| Property | Value |
|----------|-------|
| **Technology** | Nginx |
| **Role** | SSL termination, rate limiting, static file serving, reverse proxy to FastAPI |
| **Why** | Battle-tested; excellent performance for static assets; configurable rate limiting |

---

## Development Tooling

| Tool | Purpose | Version |
|------|---------|---------|
| **ESLint** | JavaScript/TypeScript linting | 9.x |
| **Prettier** | Code formatting (frontend) | 3.x |
| **Black** | Python code formatter | 24.x |
| **isort** | Python import sorter | 5.x |
| **Ruff** | Fast Python linter | 0.4+ |
| **mypy** | Python static type checker | 1.x |
| **pytest** | Python testing framework | 8.x |
| **pytest-asyncio** | Async test support | 0.23+ |
| **Vitest** | Frontend unit testing | 1.x |
| **httpx** | Async HTTP client for FastAPI tests | 0.27+ |
| **pre-commit** | Git hooks for linting | 3.x |

---

## Security Considerations

| Concern | Mitigation |
|---------|-----------|
| **PHI / Health Data** | All data encrypted at rest (PostgreSQL encryption); TLS in transit |
| **Password Storage** | bcrypt with cost factor 12; never stored in plaintext |
| **API Authentication** | Short-lived JWT access tokens; refresh token rotation |
| **SQL Injection** | SQLAlchemy parameterized queries; Pydantic input validation |
| **XSS** | React escapes by default; CSP headers via Nginx |
| **CSRF** | SameSite cookies for refresh tokens; CORS restricted origins |
| **Rate Limiting** | Nginx rate limiting; FastAPI slowapi middleware |
| **Crisis Data** | Crisis alerts stored separately; restricted access |
| **LLM Prompt Injection** | Input sanitization before LangChain; output validation |

---

## Package Versions (Pinned)

### Backend (`requirements.txt` key packages)

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.29
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
langchain==0.2.0
langchain-groq==0.1.3
scikit-learn==1.4.2
pgvector==0.2.5
httpx==0.27.0
pytest==8.1.1
pytest-asyncio==0.23.6
```

### Frontend (`package.json` key packages)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0",
    "@tanstack/react-query": "^5.35.0",
    "tailwindcss": "^3.4.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "vitest": "^1.5.0",
    "eslint": "^9.0.0"
  }
}
```
