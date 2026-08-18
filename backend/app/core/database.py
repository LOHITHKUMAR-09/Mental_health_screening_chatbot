"""
Database configuration — SQLAlchemy async engine.

For local development: uses SQLite (no setup needed).
For production: uses PostgreSQL via asyncpg (set DATABASE_URL env var).
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# ── Determine database URL ────────────────────────────────────────
_raw_url = settings.DATABASE_URL

# Default to SQLite for local dev if no Postgres URL is configured
if not _raw_url or "localhost" in _raw_url and "postgresql" in _raw_url:
    # Use SQLite in the backend directory for local dev
    _db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "mindease_local.db"
    )
    db_url = f"sqlite+aiosqlite:///{_db_path}"
    _DB_TYPE = "sqlite"
elif _raw_url.startswith("postgresql://"):
    db_url = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    _DB_TYPE = "postgres"
elif _raw_url.startswith("postgresql+asyncpg"):
    db_url = _raw_url
    _DB_TYPE = "postgres"
else:
    db_url = _raw_url
    _DB_TYPE = "other"

# SQLite needs check_same_thread=False via connect_args
connect_args = {"check_same_thread": False} if _DB_TYPE == "sqlite" else {}

engine = create_async_engine(
    db_url,
    echo=settings.APP_ENV == "development",
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency to get a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

