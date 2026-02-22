import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True
    )
    clinic_procedure_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinic_procedures.id"), nullable=True
    )

    # Schedule
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    booking_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / confirmed / completed / cancelled / no_show

    # Amounts
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(5), default="KRW")
    deposit_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    remaining_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    # Consultation protocol state
    protocol_state: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship()  # noqa: F821
    conversation: Mapped["Conversation | None"] = relationship()  # noqa: F821
    clinic_procedure: Mapped["ClinicProcedure | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Booking {self.id} status={self.status}>"
