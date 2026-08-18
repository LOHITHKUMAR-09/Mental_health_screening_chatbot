"""User model — students, counselors, and admins."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, PyEnum):
    STUDENT   = "student"
    COUNSELOR = "counselor"
    ADMIN     = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str]          = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str]  = mapped_column(String(255), nullable=True)
    role: Mapped[str]           = mapped_column(String(20), default="student")
    is_anonymous: Mapped[bool]  = mapped_column(Boolean, default=False)
    is_active: Mapped[bool]     = mapped_column(Boolean, default=True)
    full_name: Mapped[str]      = mapped_column(String(255), nullable=True)
    year_of_study: Mapped[int]  = mapped_column(Integer, nullable=True)
    major: Mapped[str]          = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")  # noqa: F821
