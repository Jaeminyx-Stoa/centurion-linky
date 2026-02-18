import uuid
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.payment import Payment
from app.models.settlement import Settlement


class SettlementService:
    """Monthly settlement calculation for clinics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_monthly_settlement(
        self, clinic_id: uuid.UUID, year: int, month: int
    ) -> Settlement:
        """Generate or return existing settlement for a clinic's given period."""
        # Check if already exists (idempotent)
        existing = await self.db.execute(
            select(Settlement).where(
                Settlement.clinic_id == clinic_id,
                Settlement.period_year == year,
                Settlement.period_month == month,
            )
        )
        settlement = existing.scalar_one_or_none()
        if settlement is not None:
            return settlement

        # Get clinic's commission rate
        clinic_result = await self.db.execute(
            select(Clinic).where(Clinic.id == clinic_id)
        )
        clinic = clinic_result.scalar_one()

        # Aggregate completed payments in period
        agg_result = await self.db.execute(
            select(
                func.coalesce(func.sum(Payment.amount), Decimal("0.00")),
                func.count(Payment.id),
            ).where(
                Payment.clinic_id == clinic_id,
                Payment.status == "completed",
                extract("year", Payment.paid_at) == year,
                extract("month", Payment.paid_at) == month,
            )
        )
        row = agg_result.one()
        total_amount = row[0] or Decimal("0.00")
        total_count = row[1] or 0

        # Calculate commission and VAT
        commission = total_amount * (clinic.commission_rate / Decimal("100"))
        vat = commission * Decimal("0.10")

        settlement = Settlement(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            period_year=year,
            period_month=month,
            total_payment_amount=total_amount,
            commission_rate=clinic.commission_rate,
            commission_amount=commission,
            vat_amount=vat,
            total_settlement=commission + vat,
            total_payment_count=total_count,
            status="pending",
        )
        self.db.add(settlement)
        await self.db.flush()
        return settlement

    async def generate_all_settlements(
        self, year: int, month: int
    ) -> list[Settlement]:
        """Generate settlements for all active clinics."""
        clinic_result = await self.db.execute(
            select(Clinic).where(Clinic.is_active.is_(True))
        )
        clinics = clinic_result.scalars().all()

        settlements = []
        for clinic in clinics:
            s = await self.generate_monthly_settlement(clinic.id, year, month)
            settlements.append(s)
        return settlements
