"""CrisisEvent model - logs of detected crisis triggers."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CrisisEvent(Base):
    __tablename__ = "crisis_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str]      = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    trigger_type: Mapped[str]    = mapped_column(String(50), nullable=True)
    trigger_phrase: Mapped[str]  = mapped_column(String(255), nullable=True)
    confidence: Mapped[float]    = mapped_column(Float, default=1.0)
    response_sent: Mapped[str]   = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["ScreeningSession"] = relationship("ScreeningSession", back_populates="crisis_events")
