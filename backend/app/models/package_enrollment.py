import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PackageEnrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "package_enrollments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    package_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("procedure_packages.id"), nullable=False, index=True
    )

    # active / completed / cancelled / paused
    status: Mapped[str] = mapped_column(String(20), default="active")
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sessions_completed: Mapped[int] = mapped_column(Integer, default=0)
    next_session_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    package: Mapped["ProcedurePackage"] = relationship(  # noqa: F821
        back_populates="enrollments"
    )
    sessions: Mapped[list["PackageSession"]] = relationship(  # noqa: F821
        back_populates="enrollment"
    )
    customer: Mapped["Customer"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<PackageEnrollment {self.id} status={self.status}>"
