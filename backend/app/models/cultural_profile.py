from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CulturalProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cultural_profiles"

    country_code: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)

    style_prompt: Mapped[str | None] = mapped_column(Text)
    preferred_expressions: Mapped[dict] = mapped_column(JSONB, default=list)
    avoided_expressions: Mapped[dict] = mapped_column(JSONB, default=list)

    emoji_level: Mapped[str] = mapped_column(String(10), default="medium")
    # 'low', 'medium', 'high'
    formality_level: Mapped[str] = mapped_column(String(10), default="polite")
    # 'casual', 'polite', 'formal'

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<CulturalProfile {self.country_code}>"
