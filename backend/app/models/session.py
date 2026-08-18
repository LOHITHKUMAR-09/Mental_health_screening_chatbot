"""Session model — a single screening interaction."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str]         = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    current_state: Mapped[str]   = mapped_column(String(50), default="greeting")
    is_complete: Mapped[bool]    = mapped_column(Boolean, default=False)
    session_number: Mapped[int]  = mapped_column(Integer, default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[datetime]   = mapped_column(DateTime, nullable=True)

    user: Mapped["User"]                              = relationship("User", back_populates="sessions")  # noqa: F821
    screening_responses: Mapped[list["ScreeningResponse"]] = relationship("ScreeningResponse", back_populates="session")  # noqa: F821
    risk_score: Mapped["RiskScore"]                   = relationship("RiskScore", back_populates="session", uselist=False)  # noqa: F821
    crisis_events: Mapped[list["CrisisEvent"]]        = relationship("CrisisEvent", back_populates="session")  # noqa: F821
