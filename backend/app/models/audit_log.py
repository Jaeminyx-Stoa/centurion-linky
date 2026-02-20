import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    # Action info
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. 'create', 'update', 'delete', 'login', 'logout', 'toggle_ai', 'export'

    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. 'booking', 'payment', 'conversation', 'messenger_account', 'ai_persona'

    resource_id: Mapped[str | None] = mapped_column(String(100))

    # Details
    description: Mapped[str | None] = mapped_column(Text)
    changes: Mapped[dict | None] = mapped_column(JSONB)
    # e.g. {"field": "status", "old": "scheduled", "new": "cancelled"}

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.resource_type}/{self.resource_id}>"
