"""Screening session model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    # State machine: greeting|consent|background|phq9|gad7|pss10|results
    current_state: Mapped[str] = mapped_column(String(50), default="greeting")
    session_number: Mapped[int] = mapped_column(default=1)  # for returning users

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")  # noqa: F821
    screening_responses: Mapped[list["ScreeningResponse"]] = relationship(  # noqa: F821
        "ScreeningResponse", back_populates="session"
    )
    risk_score: Mapped["RiskScore"] = relationship("RiskScore", back_populates="session", uselist=False)  # noqa: F821
    crisis_events: Mapped[list["CrisisEvent"]] = relationship("CrisisEvent", back_populates="session")  # noqa: F821
