import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ABTest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ab_tests"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # What is being tested: "prompt", "greeting", "sales_strategy"
    test_type: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft → active → completed → archived

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    variants: Mapped[list["ABTestVariant"]] = relationship(
        back_populates="ab_test", cascade="all, delete-orphan"
    )
    results: Mapped[list["ABTestResult"]] = relationship(
        back_populates="ab_test", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ABTest {self.name} status={self.status}>"


class ABTestVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ab_test_variants"

    ab_test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "A", "B", "Control"

    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Variant-specific configuration (prompt text, strategy, etc.)

    weight: Mapped[int] = mapped_column(Integer, default=50)
    # Traffic allocation weight (percentage)

    # Relationships
    ab_test: Mapped["ABTest"] = relationship(back_populates="variants")

    def __repr__(self) -> str:
        return f"<ABTestVariant {self.name} test={self.ab_test_id}>"


class ABTestResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ab_test_results"

    ab_test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ab_test_variants.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False
    )

    # Outcome
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    # "booked", "paid", "abandoned", "escalated"

    outcome_data: Mapped[dict | None] = mapped_column(JSONB)
    # Additional metrics: satisfaction_score, response_time, etc.

    # Relationships
    ab_test: Mapped["ABTest"] = relationship(back_populates="results")
    variant: Mapped["ABTestVariant"] = relationship()

    def __repr__(self) -> str:
        return f"<ABTestResult test={self.ab_test_id} outcome={self.outcome}>"
