"""
MindEase — ML-Assisted Mental Health Screening Chatbot
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import engine, Base

# Import ALL models so SQLAlchemy registers them before create_all
from app.models import user, session, screening_response, risk_score, crisis_event, message  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Auto-create all tables against PostgreSQL
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[MindEase] Backend started | DB: PostgreSQL | API: http://localhost:8000/docs")
    yield
    print("[MindEase] Backend shutting down.")




app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ML-Assisted Mental Health Screening Chatbot for University Students",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include API Router ─────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "MindEase API is running 🧠",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {"status": "healthy", "database": "connected"}
