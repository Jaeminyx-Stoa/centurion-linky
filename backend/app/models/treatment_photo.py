import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TreatmentPhoto(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "treatment_photos"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True, index=True
    )
    procedure_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("procedures.id"), nullable=True
    )

    # Photo metadata
    photo_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # before / after / progress
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)

    # Timing
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    days_after_procedure: Mapped[int | None] = mapped_column(Integer)

    # Consent & approval
    is_consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    is_portfolio_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Pair linking (before ↔ after)
    pair_id: Mapped[uuid.UUID | None] = mapped_column(index=True)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship()  # noqa: F821
    booking: Mapped["Booking | None"] = relationship()  # noqa: F821
    procedure: Mapped["Procedure | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<TreatmentPhoto {self.photo_type} {self.id}>"
