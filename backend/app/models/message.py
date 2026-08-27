"""ChatMessage model - logs student-bot dialogue per session."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str]       = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    sender: Mapped[str]           = mapped_column(String(10), nullable=False)  # "user" | "bot" | "system"
    content: Mapped[str]          = mapped_column(Text, nullable=False)
    state: Mapped[str]            = mapped_column(String(50), nullable=False, default="greeting")
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["ScreeningSession"] = relationship("ScreeningSession", back_populates="messages")
