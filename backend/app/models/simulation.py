import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SimulationSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "simulation_sessions"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Persona used
    persona_name: Mapped[str] = mapped_column(String(100), nullable=False)
    persona_config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Session config
    max_rounds: Mapped[int] = mapped_column(Integer, default=20)
    actual_rounds: Mapped[int] = mapped_column(Integer, default=0)

    # Status: pending → running → completed → failed
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Messages log
    messages: Mapped[list | None] = mapped_column(JSONB)
    # [{"role": "customer"|"ai", "content": "...", "round": 1}, ...]

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    result: Mapped["SimulationResult | None"] = relationship(
        back_populates="session", uselist=False
    )

    def __repr__(self) -> str:
        return f"<SimulationSession {self.persona_name} status={self.status}>"


class SimulationResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "simulation_results"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Outcome
    booked: Mapped[bool] = mapped_column(Boolean, default=False)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    abandoned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Scores
    satisfaction_score: Mapped[int | None] = mapped_column(Integer)
    response_quality_score: Mapped[int | None] = mapped_column(Integer)

    # Analysis
    exit_reason: Mapped[str | None] = mapped_column(String(100))
    strategies_used: Mapped[list | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    session: Mapped["SimulationSession"] = relationship(back_populates="result")

    def __repr__(self) -> str:
        return f"<SimulationResult session={self.session_id} booked={self.booked}>"
