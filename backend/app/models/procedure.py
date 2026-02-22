import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Procedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "procedures"

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("procedure_categories.id"), nullable=True
    )

    # Names (multilingual)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200))
    name_ja: Mapped[str | None] = mapped_column(String(200))
    name_zh: Mapped[str | None] = mapped_column(String(200))
    name_vi: Mapped[str | None] = mapped_column(String(200))

    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    # Descriptions
    description_ko: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    effects_ko: Mapped[str | None] = mapped_column(Text)

    # Time-related (textbook defaults)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    effect_duration: Mapped[str | None] = mapped_column(String(100))
    downtime_days: Mapped[int | None] = mapped_column(Integer)
    min_interval_days: Mapped[int | None] = mapped_column(Integer)

    # Side effects
    common_side_effects: Mapped[str | None] = mapped_column(Text)
    rare_side_effects: Mapped[str | None] = mapped_column(Text)
    dangerous_side_effects: Mapped[str | None] = mapped_column(Text)

    # Precautions
    precautions_before: Mapped[str | None] = mapped_column(Text)
    precautions_during: Mapped[str | None] = mapped_column(Text)
    precautions_after: Mapped[str | None] = mapped_column(Text)

    # Pain/anesthesia
    pain_level: Mapped[int | None] = mapped_column(Integer)
    pain_type: Mapped[str | None] = mapped_column(String(100))
    anesthesia_options: Mapped[str | None] = mapped_column(Text)
    anesthesia_details: Mapped[dict | None] = mapped_column(JSONB)
    contraindications: Mapped[dict | None] = mapped_column(JSONB)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    # Relationships
    category: Mapped["ProcedureCategory | None"] = relationship(  # noqa: F821
        back_populates="procedures"
    )
    clinic_procedures: Mapped[list["ClinicProcedure"]] = relationship(  # noqa: F821
        back_populates="procedure"
    )

    def __repr__(self) -> str:
        return f"<Procedure {self.slug}>"
