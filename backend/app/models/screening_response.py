"""ScreeningResponse model - individual questionnaire item answers."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScreeningResponse(Base):
    __tablename__ = "screening_responses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str]       = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    instrument: Mapped[str]       = mapped_column(String(10), nullable=False)
    item_number: Mapped[int]      = mapped_column(Integer, nullable=False)
    response_value: Mapped[int]   = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["ScreeningSession"] = relationship("ScreeningSession", back_populates="screening_responses")
