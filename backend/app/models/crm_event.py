import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CRMEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crm_events"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payments.id"), nullable=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True
    )

    # Event type
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # receipt / review_request / aftercare / survey_1 / survey_2 / survey_3 / revisit_reminder

    # Schedule
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # scheduled / sent / completed / cancelled / failed

    # Content
    message_content: Mapped[str | None] = mapped_column(Text)

    # Response data
    response: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship()  # noqa: F821
    payment: Mapped["Payment | None"] = relationship()  # noqa: F821
    booking: Mapped["Booking | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<CRMEvent {self.id} type={self.event_type} status={self.status}>"
