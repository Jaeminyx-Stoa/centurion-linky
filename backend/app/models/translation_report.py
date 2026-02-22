import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TranslationReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "translation_reports"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id"), nullable=True
    )
    reported_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    # Translation content
    source_language: Mapped[str] = mapped_column(String(10), nullable=False)
    target_language: Mapped[str] = mapped_column(String(10), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str | None] = mapped_column(Text)

    # Error classification
    error_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # wrong_term / wrong_meaning / awkward / omission / other
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    # critical / minor

    # Optional link to medical term
    medical_term_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_terms.id"), nullable=True
    )

    # Review workflow
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / reviewed / resolved / dismissed
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    reporter: Mapped["User"] = relationship(foreign_keys=[reported_by])  # noqa: F821
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewer_id])  # noqa: F821
    medical_term: Mapped["MedicalTerm | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<TranslationReport {self.error_type} {self.status}>"
