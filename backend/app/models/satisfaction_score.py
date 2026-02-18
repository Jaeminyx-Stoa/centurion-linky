import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class SatisfactionScore(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "satisfaction_scores"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Score (0~100) and level
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    # green / yellow / orange / red

    # Signal analysis details
    language_signals: Mapped[dict | None] = mapped_column(JSONB)
    behavior_signals: Mapped[dict | None] = mapped_column(JSONB)
    flow_signals: Mapped[dict | None] = mapped_column(JSONB)

    # Supervisor override
    supervisor_override: Mapped[int | None] = mapped_column(Integer)
    supervisor_note: Mapped[str | None] = mapped_column(Text)
    supervised_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    supervised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Alert tracking
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship()  # noqa: F821
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    supervisor: Mapped["User | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<SatisfactionScore {self.id} score={self.score} level={self.level}>"
