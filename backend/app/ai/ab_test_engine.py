import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ab_test import ABTest, ABTestResult, ABTestVariant


class ABTestEngine:
    """A/B test variant selection and outcome tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def select_variant(
        self, test_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> ABTestVariant | None:
        """Select a variant for a conversation using hash-based consistent assignment."""
        # Get active test with variants
        test_result = await self.db.execute(
            select(ABTest).where(
                ABTest.id == test_id,
                ABTest.is_active.is_(True),
            )
        )
        test = test_result.scalar_one_or_none()
        if test is None:
            return None

        variants_result = await self.db.execute(
            select(ABTestVariant)
            .where(ABTestVariant.ab_test_id == test_id)
            .order_by(ABTestVariant.created_at)
        )
        variants = list(variants_result.scalars().all())
        if not variants:
            return None

        # Hash-based consistent assignment
        idx = hash(str(conversation_id)) % len(variants)
        return variants[idx]

    async def record_outcome(
        self,
        test_id: uuid.UUID,
        variant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        outcome: str,
        outcome_data: dict | None = None,
    ) -> ABTestResult:
        """Record the outcome of a conversation in an A/B test."""
        result = ABTestResult(
            id=uuid.uuid4(),
            ab_test_id=test_id,
            variant_id=variant_id,
            conversation_id=conversation_id,
            outcome=outcome,
            outcome_data=outcome_data,
        )
        self.db.add(result)
        await self.db.flush()
        return result

    async def get_stats(self, test_id: uuid.UUID) -> list[dict]:
        """Get per-variant statistics for a test."""
        # Get variants
        variants_result = await self.db.execute(
            select(ABTestVariant).where(ABTestVariant.ab_test_id == test_id)
        )
        variants = list(variants_result.scalars().all())

        stats = []
        for variant in variants:
            # Count outcomes per variant
            total_result = await self.db.execute(
                select(func.count(ABTestResult.id)).where(
                    ABTestResult.variant_id == variant.id
                )
            )
            total = total_result.scalar() or 0

            positive_result = await self.db.execute(
                select(func.count(ABTestResult.id)).where(
                    ABTestResult.variant_id == variant.id,
                    ABTestResult.outcome.in_(["booked", "paid"]),
                )
            )
            positive = positive_result.scalar() or 0

            conversion_rate = (positive / total * 100) if total > 0 else 0.0

            stats.append({
                "variant_id": str(variant.id),
                "variant_name": variant.name,
                "total_conversations": total,
                "positive_outcomes": positive,
                "conversion_rate": round(conversion_rate, 2),
            })

        return stats
