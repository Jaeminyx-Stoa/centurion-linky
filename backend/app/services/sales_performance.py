import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic_procedure import ClinicProcedure
from app.models.procedure_pricing import ProcedurePricing

# Difficulty score → points (30 max, easier = more points)
DIFFICULTY_MAP = {1: 30, 2: 24, 3: 18, 4: 12, 5: 6}

# Clinic preference → points (30 max, recommended = more points)
PREFERENCE_MAP = {1: 30, 2: 15, 3: 0}

DEFAULT_MARGIN_SCORE = Decimal("20")
DEFAULT_DIFFICULTY_SCORE = 18
DEFAULT_PREFERENCE_SCORE = 15


class SalesPerformanceCalculator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate(self, clinic_id: uuid.UUID) -> dict[uuid.UUID, Decimal]:
        """Calculate sales performance scores for all clinic procedures.

        Score (100 max) = margin_score(40) + difficulty_score(30) + preference_score(30)

        Returns: {clinic_procedure_id: score}
        """
        # 1. Load all active clinic procedures
        result = await self.db.execute(
            select(ClinicProcedure).where(
                ClinicProcedure.clinic_id == clinic_id,
                ClinicProcedure.is_active.is_(True),
            )
        )
        procedures = list(result.scalars().all())
        if not procedures:
            return {}

        # 2. Load all active pricing
        cp_ids = [p.id for p in procedures]
        result = await self.db.execute(
            select(ProcedurePricing).where(
                ProcedurePricing.clinic_procedure_id.in_(cp_ids),
                ProcedurePricing.is_active.is_(True),
            )
        )
        pricing_by_cp: dict[uuid.UUID, ProcedurePricing] = {}
        for pricing in result.scalars().all():
            pricing_by_cp[pricing.clinic_procedure_id] = pricing

        # 3. Calculate margin per minute
        margins: list[tuple[uuid.UUID, Decimal]] = []
        for p in procedures:
            pricing = pricing_by_cp.get(p.id)
            duration = p.custom_duration_minutes
            if pricing and p.material_cost and duration and duration > 0:
                price = pricing.event_price or pricing.regular_price
                margin_per_min = (price - p.material_cost) / Decimal(str(duration))
                margins.append((p.id, margin_per_min))

        # 4. Rank margins → percentile → 40 points max
        margin_scores: dict[uuid.UUID, Decimal] = {}
        if margins:
            margins.sort(key=lambda x: x[1], reverse=True)
            count = len(margins)
            for rank, (pid, _) in enumerate(margins):
                percentile = Decimal(str(1 - (rank / count))) if count > 1 else Decimal("1")
                margin_scores[pid] = round(percentile * 40, 2)

        # 5. Combine scores
        scores: dict[uuid.UUID, Decimal] = {}
        for p in procedures:
            m_score = margin_scores.get(p.id, DEFAULT_MARGIN_SCORE)
            d_score = DIFFICULTY_MAP.get(p.difficulty_score or 3, DEFAULT_DIFFICULTY_SCORE)
            pref_score = PREFERENCE_MAP.get(p.clinic_preference or 2, DEFAULT_PREFERENCE_SCORE)
            total = Decimal(str(float(m_score) + d_score + pref_score))
            scores[p.id] = min(total, Decimal("100"))

            # Update DB
            p.sales_performance_score = scores[p.id]

        await self.db.flush()
        return scores
