import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False
    )

    # Payment type
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # deposit / remaining / full / additional

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="KRW")

    # PG provider info
    pg_provider: Mapped[str | None] = mapped_column(String(50))
    pg_payment_id: Mapped[str | None] = mapped_column(String(200))
    payment_method: Mapped[str | None] = mapped_column(String(50))

    # Payment link / QR
    payment_link: Mapped[str | None] = mapped_column(String(500))
    qr_code_url: Mapped[str | None] = mapped_column(String(500))
    link_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / link_sent / completed / failed / refunded / cancelled

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metadata
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    booking: Mapped["Booking | None"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Payment {self.id} status={self.status}>"
