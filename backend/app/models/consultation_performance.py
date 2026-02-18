import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConsultationPerformance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consultation_performances"
    __table_args__ = (
        UniqueConstraint("clinic_id", "period_year", "period_month"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Period
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Total score (100 points max)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Component scores
    sales_mix_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )  # max 40
    booking_conversion_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )  # max 30
    payment_conversion_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )  # max 30

    # Rates
    booking_conversion_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    payment_conversion_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )

    # Counts
    total_consultations: Mapped[int] = mapped_column(Integer, default=0)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0)
    total_payments: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<ConsultationPerformance {self.clinic_id} {self.period_year}-{self.period_month:02d} score={self.total_score}>"
