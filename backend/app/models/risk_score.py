"""Risk score model — stores computed clinical and ML risk assessments."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, unique=True
    )

    # --- Deterministic clinical scores ---
    phq9_score: Mapped[int] = mapped_column(Integer, nullable=True)
    phq9_severity: Mapped[str] = mapped_column(String(30), nullable=True)
    gad7_score: Mapped[int] = mapped_column(Integer, nullable=True)
    gad7_severity: Mapped[str] = mapped_column(String(30), nullable=True)
    pss10_score: Mapped[int] = mapped_column(Integer, nullable=True)
    pss10_severity: Mapped[str] = mapped_column(String(30), nullable=True)

    # --- Composite rule-based risk ---
    rule_based_risk: Mapped[str] = mapped_column(String(20), nullable=True)  # low|moderate|high

    # --- ML model output ---
    ml_risk_label: Mapped[str] = mapped_column(String(20), nullable=True)  # low|moderate|high
    ml_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    shap_values: Mapped[dict] = mapped_column(JSON, nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["Session"] = relationship("Session", back_populates="risk_score")  # noqa: F821
