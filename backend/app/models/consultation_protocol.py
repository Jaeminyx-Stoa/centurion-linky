import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConsultationProtocol(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consultation_protocols"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    procedure_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("procedures.id"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # [{id, question_ko, question_en, ..., required, type, choices}]
    checklist_items: Mapped[dict | None] = mapped_column(JSONB)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<ConsultationProtocol {self.name}>"
