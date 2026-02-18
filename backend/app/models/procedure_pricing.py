import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProcedurePricing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "procedure_pricing"

    clinic_procedure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinic_procedures.id"), nullable=False
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Prices
    regular_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    event_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    discount_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    # Event period
    event_start_date: Mapped[date | None] = mapped_column(Date)
    event_end_date: Mapped[date | None] = mapped_column(Date)

    # Package
    is_package: Mapped[bool] = mapped_column(Boolean, default=False)
    package_details: Mapped[dict | None] = mapped_column(JSONB)

    # Multi-currency prices
    prices_by_currency: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Discount warning (>49%)
    discount_warning: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    clinic_procedure: Mapped["ClinicProcedure"] = relationship(  # noqa: F821
        back_populates="pricing"
    )
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<ProcedurePricing {self.id}>"
