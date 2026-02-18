import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MedicalTerm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "medical_terms"

    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinics.id"), nullable=True
    )
    # None = global term, clinic_id = clinic-specific override

    term_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    # Korean canonical term (e.g., "보톡스", "물광주사")

    translations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"ja": "ボトックス", "en": "Botox", "zh-CN": "肉毒素", "zh-TW": "肉毒桿菌", "vi": "Botox"}

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # 'procedure', 'symptom', 'body_part', 'material', 'general'

    description: Mapped[str | None] = mapped_column(Text)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<MedicalTerm {self.term_ko}>"
