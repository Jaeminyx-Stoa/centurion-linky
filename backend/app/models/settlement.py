import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Settlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "settlements"
    __table_args__ = (
        UniqueConstraint("clinic_id", "period_year", "period_month"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Period
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Amounts
    total_payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    commission_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    vat_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    total_settlement: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )

    # Counts
    total_payment_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status: pending → confirmed → paid
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Settlement {self.clinic_id} {self.period_year}-{self.period_month:02d}>"
