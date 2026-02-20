import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class Message(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Sender
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # 'customer','ai','staff'
    sender_id: Mapped[uuid.UUID | None] = mapped_column()

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), default="text")
    # 'text','image','file','payment_link','booking_card'

    # Translation
    original_language: Mapped[str | None] = mapped_column(String(10))
    translated_content: Mapped[str | None] = mapped_column(Text)
    translated_language: Mapped[str | None] = mapped_column(String(10))

    # Messenger info
    messenger_type: Mapped[str | None] = mapped_column(String(20))
    messenger_message_id: Mapped[str | None] = mapped_column(String(200))

    # AI metadata
    ai_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # Attachments
    attachments: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")  # noqa: F821
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Message {self.sender_type} in {self.conversation_id}>"
