"""Screening response model — stores individual questionnaire answers."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ScreeningResponse(Base):
    __tablename__ = "screening_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True
    )
    # Instrument: phq9 | gad7 | pss10 | wemwbs
    instrument: Mapped[str] = mapped_column(String(20), nullable=False)
    # Item number within the instrument (1-indexed)
    item_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Likert response value (instrument-dependent)
    response_value: Mapped[int] = mapped_column(Integer, nullable=False)
    responded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["Session"] = relationship("Session", back_populates="screening_responses")  # noqa: F821
