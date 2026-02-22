import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProcedurePackage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "procedure_packages"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Names (multilingual)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200))
    name_ja: Mapped[str | None] = mapped_column(String(200))
    name_zh: Mapped[str | None] = mapped_column(String(200))
    name_vi: Mapped[str | None] = mapped_column(String(200))

    description: Mapped[str | None] = mapped_column(Text)

    # Package items: [{clinic_procedure_id, sessions, interval_days}]
    items: Mapped[dict | None] = mapped_column(JSONB)

    total_sessions: Mapped[int] = mapped_column(Integer, default=1)
    package_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    discount_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    enrollments: Mapped[list["PackageEnrollment"]] = relationship(  # noqa: F821
        back_populates="package"
    )

    def __repr__(self) -> str:
        return f"<ProcedurePackage {self.name_ko}>"
