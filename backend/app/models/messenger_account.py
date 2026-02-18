import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MessengerAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messenger_accounts"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False
    )
    messenger_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 'telegram','instagram','facebook','whatsapp','line','kakao'

    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))

    credentials: Mapped[dict] = mapped_column(JSONB, nullable=False)
    webhook_url: Mapped[str | None] = mapped_column(String(500))
    webhook_secret: Mapped[str | None] = mapped_column(String(200))

    target_countries: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="messenger_accounts")  # noqa: F821
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        back_populates="messenger_account"
    )

    def __repr__(self) -> str:
        return f"<MessengerAccount {self.messenger_type}:{self.account_name}>"
