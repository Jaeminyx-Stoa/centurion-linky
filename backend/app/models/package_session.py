import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PackageSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "package_sessions"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("package_enrollments.id"), nullable=False, index=True
    )
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)
    clinic_procedure_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinic_procedures.id"), nullable=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True
    )

    # pending / completed / cancelled / skipped
    status: Mapped[str] = mapped_column(String(20), default="pending")
    scheduled_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    enrollment: Mapped["PackageEnrollment"] = relationship(  # noqa: F821
        back_populates="sessions"
    )
    booking: Mapped["Booking | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<PackageSession {self.enrollment_id}#{self.session_number}>"
