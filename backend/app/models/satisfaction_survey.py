import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class SatisfactionSurvey(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "satisfaction_surveys"
    __table_args__ = (
        CheckConstraint(
            "satisfaction_score BETWEEN 1 AND 5", name="ck_satisfaction_score"
        ),
        CheckConstraint("nps_score BETWEEN 0 AND 10", name="ck_nps_score"),
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id"), nullable=True
    )
    crm_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("crm_events.id"), nullable=True
    )

    # Survey round: 1 (직후), 2 (7일), 3 (14일)
    survey_round: Mapped[int] = mapped_column(Integer, nullable=False)

    # Satisfaction score (1~5)
    satisfaction_score: Mapped[int | None] = mapped_column(Integer)

    # Round 2: revisit intention
    revisit_intention: Mapped[str | None] = mapped_column(String(10))
    # yes / maybe / no

    # Round 3: NPS (0~10)
    nps_score: Mapped[int | None] = mapped_column(Integer)

    # Feedback
    feedback_text: Mapped[str | None] = mapped_column(Text)

    # Round 2: side effects
    side_effects_reported: Mapped[str | None] = mapped_column(Text)

    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship()  # noqa: F821
    customer: Mapped["Customer"] = relationship()  # noqa: F821
    booking: Mapped["Booking | None"] = relationship()  # noqa: F821
    crm_event: Mapped["CRMEvent | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<SatisfactionSurvey {self.id} round={self.survey_round}>"
