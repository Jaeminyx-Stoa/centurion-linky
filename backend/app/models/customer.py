import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("clinic_id", "messenger_type", "messenger_user_id"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    # Messenger identification
    messenger_type: Mapped[str] = mapped_column(String(20), nullable=False)
    messenger_user_id: Mapped[str] = mapped_column(String(200), nullable=False)

    # Profile
    name: Mapped[str | None] = mapped_column(String(200))
    display_name: Mapped[str | None] = mapped_column(String(200))
    profile_image: Mapped[str | None] = mapped_column(String(500))

    # Country / Language
    country_code: Mapped[str | None] = mapped_column(String(5))
    language_code: Mapped[str | None] = mapped_column(String(10))
    timezone: Mapped[str | None] = mapped_column(String(50))

    # Contact
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(200))

    # Tags / Notes
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), default=list)
    notes: Mapped[str | None] = mapped_column(Text)

    # Health information
    medical_conditions: Mapped[dict | None] = mapped_column(JSONB)
    allergies: Mapped[dict | None] = mapped_column(JSONB)
    medications: Mapped[dict | None] = mapped_column(JSONB)

    # Stats (cached)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0)
    total_payments: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    last_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Churn/revisit prediction (cached)
    churn_risk_score: Mapped[int | None] = mapped_column(Integer)
    predicted_next_visit: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        back_populates="customer"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.messenger_type}:{self.messenger_user_id}>"
