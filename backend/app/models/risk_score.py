"""RiskScore model - computed scores per session."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str]       = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False, unique=True, index=True)
    phq9_score: Mapped[int]       = mapped_column(Integer, nullable=True)
    phq9_severity: Mapped[str]    = mapped_column(String(30), nullable=True)
    gad7_score: Mapped[int]       = mapped_column(Integer, nullable=True)
    gad7_severity: Mapped[str]    = mapped_column(String(30), nullable=True)
    pss10_score: Mapped[int]      = mapped_column(Integer, nullable=True)
    pss10_severity: Mapped[str]   = mapped_column(String(30), nullable=True)
    rule_based_risk: Mapped[str]  = mapped_column(String(20), nullable=True)
    ml_risk_label: Mapped[str]    = mapped_column(String(20), nullable=True)
    ml_confidence: Mapped[float]  = mapped_column(Float, nullable=True)
    shap_values: Mapped[str]      = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["ScreeningSession"] = relationship("ScreeningSession", back_populates="risk_score")
