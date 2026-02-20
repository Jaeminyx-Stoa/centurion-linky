import uuid

from sqlalchemy import ARRAY, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResponseLibrary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "response_library"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # 'pricing', 'procedure', 'booking', 'aftercare', 'general'
    subcategory: Mapped[str | None] = mapped_column(String(50))

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="ko")

    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<ResponseLibrary {self.category}/{self.subcategory}>"
