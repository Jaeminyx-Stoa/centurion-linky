import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SideEffectKeyword(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "side_effect_keywords"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    # "ko" / "en" / "ja" / "zh" / "vi"

    keywords: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # ["아프다", "부어오르다", "빨갛다", "멍", ...]

    severity: Mapped[str] = mapped_column(String(10), default="normal")
    # "urgent" / "normal"

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<SideEffectKeyword {self.id} lang={self.language} severity={self.severity}>"
