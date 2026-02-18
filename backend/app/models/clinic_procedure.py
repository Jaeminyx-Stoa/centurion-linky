import uuid
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ClinicProcedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clinic_procedures"
    __table_args__ = (
        UniqueConstraint("clinic_id", "procedure_id"),
        CheckConstraint("difficulty_score BETWEEN 1 AND 5", name="ck_difficulty"),
        CheckConstraint("clinic_preference BETWEEN 1 AND 3", name="ck_preference"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    procedure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("procedures.id"), nullable=False
    )

    # Custom overrides (NULL = use base procedure default)
    custom_description: Mapped[str | None] = mapped_column(Text)
    custom_effects: Mapped[str | None] = mapped_column(Text)
    custom_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    custom_effect_duration: Mapped[str | None] = mapped_column(String(100))
    custom_downtime_days: Mapped[int | None] = mapped_column(Integer)
    custom_min_interval_days: Mapped[int | None] = mapped_column(Integer)
    custom_precautions_before: Mapped[str | None] = mapped_column(Text)
    custom_precautions_during: Mapped[str | None] = mapped_column(Text)
    custom_precautions_after: Mapped[str | None] = mapped_column(Text)
    custom_pain_level: Mapped[int | None] = mapped_column(Integer)
    custom_anesthesia_options: Mapped[str | None] = mapped_column(Text)

    # Cross-sell / upsell
    cross_sell_procedure_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(PgUUID(as_uuid=True)), default=list
    )
    upsell_procedure_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(PgUUID(as_uuid=True)), default=list
    )
    incompatible_procedure_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(PgUUID(as_uuid=True)), default=list
    )
    sequence_notes: Mapped[str | None] = mapped_column(Text)

    # Business data (internal, not exposed to customers)
    material_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    difficulty_score: Mapped[int | None] = mapped_column(Integer)
    clinic_preference: Mapped[int | None] = mapped_column(Integer)

    # Auto-calculated sales performance score
    sales_performance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    procedure: Mapped["Procedure"] = relationship(  # noqa: F821
        back_populates="clinic_procedures"
    )
    pricing: Mapped[list["ProcedurePricing"]] = relationship(  # noqa: F821
        back_populates="clinic_procedure"
    )

    def __repr__(self) -> str:
        return f"<ClinicProcedure {self.id}>"
