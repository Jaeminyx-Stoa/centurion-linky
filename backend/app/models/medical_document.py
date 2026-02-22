import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MedicalDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "medical_documents"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True, index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id"), nullable=True, index=True
    )

    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # chart_draft / consent_form

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    content: Mapped[dict | None] = mapped_column(JSONB)

    language: Mapped[str] = mapped_column(String(5), default="ko")

    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft / reviewed / signed / archived

    generated_by: Mapped[str] = mapped_column(String(20), default="ai")
    # ai / staff

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship()  # noqa: F821
    booking: Mapped["Booking | None"] = relationship()  # noqa: F821
    conversation: Mapped["Conversation | None"] = relationship()  # noqa: F821
    reviewer: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[reviewed_by]
    )

    def __repr__(self) -> str:
        return f"<MedicalDocument {self.id} type={self.document_type} status={self.status}>"
