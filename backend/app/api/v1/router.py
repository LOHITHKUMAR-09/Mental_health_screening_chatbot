"""API v1 main router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, sessions, chat, screening, results

api_router = APIRouter()

api_router.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
api_router.include_router(sessions.router,  prefix="/sessions",  tags=["Sessions"])
api_router.include_router(chat.router,      prefix="/chat",      tags=["Chat"])
api_router.include_router(screening.router, prefix="/screening", tags=["Screening"])
api_router.include_router(results.router,   prefix="/results",   tags=["Results"])
