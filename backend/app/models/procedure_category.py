import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class ProcedureCategory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "procedure_categories"

    name_ko: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    name_ja: Mapped[str | None] = mapped_column(String(100))
    name_zh: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("procedure_categories.id"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Self-referential relationship
    children: Mapped[list["ProcedureCategory"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent: Mapped["ProcedureCategory | None"] = relationship(
        back_populates="children",
        remote_side="ProcedureCategory.id",
    )

    # Procedures in this category
    procedures: Mapped[list["Procedure"]] = relationship(  # noqa: F821
        back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<ProcedureCategory {self.slug}>"
