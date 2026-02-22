import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking
from app.models.clinic_procedure import ClinicProcedure
from app.models.crm_event import CRMEvent
from app.models.followup_rule import FollowupRule
from app.models.side_effect_keyword import SideEffectKeyword


class FollowupService:
    """Manages post-procedure followup scheduling and side-effect detection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_followups(self, booking_id: uuid.UUID) -> list[CRMEvent]:
        """Schedule followup CRM events when a booking is completed.

        Loads the booking's procedure and finds matching followup rules
        (procedure-specific + global), then creates CRMEvent for each.
        """
        result = await self.db.execute(
            select(Booking)
            .options(selectinload(Booking.clinic_procedure))
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            return []

        # Determine procedure_id from clinic_procedure
        procedure_id = None
        if booking.clinic_procedure_id:
            cp = booking.clinic_procedure
            if cp:
                procedure_id = cp.procedure_id

        # Find matching rules: procedure-specific + global (procedure_id IS NULL)
        conditions = [
            FollowupRule.clinic_id == booking.clinic_id,
            FollowupRule.is_active.is_(True),
        ]
        if procedure_id:
            conditions.append(
                or_(
                    FollowupRule.procedure_id == procedure_id,
                    FollowupRule.procedure_id.is_(None),
                )
            )
        else:
            conditions.append(FollowupRule.procedure_id.is_(None))

        rules_result = await self.db.execute(
            select(FollowupRule)
            .where(*conditions)
            .order_by(FollowupRule.sort_order)
        )
        rules = list(rules_result.scalars().all())

        now = datetime.now(timezone.utc)
        events = []
        for rule in rules:
            offset = timedelta(days=rule.delay_days, hours=rule.delay_hours)
            event = CRMEvent(
                id=uuid.uuid4(),
                clinic_id=booking.clinic_id,
                customer_id=booking.customer_id,
                booking_id=booking.id,
                event_type=rule.event_type,
                scheduled_at=now + offset,
                status="scheduled",
                message_content=self._resolve_template(rule.message_template),
            )
            self.db.add(event)
            events.append(event)

        await self.db.flush()
        return events

    async def check_side_effects(
        self,
        message_content: str,
        clinic_id: uuid.UUID,
        customer_language: str,
    ) -> dict | None:
        """Check message content against clinic side-effect keywords.

        Returns alert dict with matched_keywords and severity, or None if no match.
        """
        if not message_content:
            return None

        result = await self.db.execute(
            select(SideEffectKeyword).where(
                SideEffectKeyword.clinic_id == clinic_id,
                SideEffectKeyword.language == customer_language,
            )
        )
        keyword_sets = list(result.scalars().all())

        content_lower = message_content.lower()
        best_severity = None
        matched = []

        for kw_set in keyword_sets:
            keywords = kw_set.keywords
            if not isinstance(keywords, list):
                continue
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    matched.append(keyword)
                    if kw_set.severity == "urgent":
                        best_severity = "urgent"
                    elif best_severity is None:
                        best_severity = "normal"

        if not matched:
            return None

        return {
            "matched_keywords": matched,
            "severity": best_severity or "normal",
        }

    @staticmethod
    def _resolve_template(
        template: dict | None, language: str = "ko"
    ) -> str | None:
        """Resolve a message template to the preferred language."""
        if not template:
            return None
        return template.get(language) or template.get("ko") or next(iter(template.values()), None)
