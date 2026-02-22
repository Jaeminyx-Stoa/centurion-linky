import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FollowupRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "followup_rules"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    procedure_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("procedures.id"), nullable=True, index=True
    )

    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # recovery_check / side_effect_check / result_check / retouch_reminder

    delay_days: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_hours: Mapped[int] = mapped_column(Integer, default=0)

    message_template: Mapped[dict | None] = mapped_column(JSONB)
    # {"ko": "...", "en": "...", "ja": "...", "zh": "...", "vi": "..."}

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    procedure: Mapped["Procedure | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<FollowupRule {self.id} type={self.event_type} delay={self.delay_days}d>"
