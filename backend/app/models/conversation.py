import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    messenger_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messenger_accounts.id"), nullable=False, index=True
    )

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")
    # 'active','waiting','resolved','archived'

    # AI / Manual mode
    ai_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Satisfaction (cached)
    satisfaction_score: Mapped[int | None] = mapped_column(Integer)
    satisfaction_level: Mapped[str | None] = mapped_column(String(10))
    # 'green','yellow','orange','red'

    # Metadata
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_message_preview: Mapped[str | None] = mapped_column(Text)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)

    # AI-generated summary
    summary: Mapped[str | None] = mapped_column(Text)
    detected_intents: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship(back_populates="conversations")  # noqa: F821
    messenger_account: Mapped["MessengerAccount"] = relationship(  # noqa: F821
        back_populates="conversations"
    )
    assigned_user: Mapped["User | None"] = relationship()  # noqa: F821
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        back_populates="conversation", order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} status={self.status}>"
