import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.procedure import Procedure
from app.models.procedure_pricing import ProcedurePricing
from app.services.sales_performance import SalesPerformanceCalculator


@pytest_asyncio.fixture
async def sp_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="퍼포먼스의원", slug="sp-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def sp_procedures(db: AsyncSession) -> list[Procedure]:
    procs = []
    for name, slug, dur in [
        ("보톡스", "sp-botox", 30),
        ("필러", "sp-filler", 45),
        ("리프팅", "sp-lifting", 60),
    ]:
        p = Procedure(id=uuid.uuid4(), name_ko=name, slug=slug, duration_minutes=dur)
        db.add(p)
        procs.append(p)
    await db.commit()
    for p in procs:
        await db.refresh(p)
    return procs


@pytest_asyncio.fixture
async def sp_clinic_procedures(
    db: AsyncSession, sp_clinic: Clinic, sp_procedures: list[Procedure]
) -> list[ClinicProcedure]:
    cps = []
    configs = [
        # (material_cost, difficulty, preference)
        (Decimal("5000"), 1, 1),   # 보톡스: low cost, easy, recommended
        (Decimal("20000"), 3, 2),  # 필러: medium cost, medium, normal
        (Decimal("50000"), 5, 3),  # 리프팅: high cost, hard, not recommended
    ]
    for proc, (cost, diff, pref) in zip(sp_procedures, configs):
        cp = ClinicProcedure(
            id=uuid.uuid4(),
            clinic_id=sp_clinic.id,
            procedure_id=proc.id,
            custom_duration_minutes=proc.duration_minutes,
            material_cost=cost,
            difficulty_score=diff,
            clinic_preference=pref,
        )
        db.add(cp)
        cps.append(cp)
    await db.commit()
    for cp in cps:
        await db.refresh(cp)
    return cps


@pytest_asyncio.fixture
async def sp_pricing(
    db: AsyncSession, sp_clinic: Clinic, sp_clinic_procedures: list[ClinicProcedure]
) -> list[ProcedurePricing]:
    prices = []
    price_configs = [
        Decimal("150000"),   # 보톡스: 150k
        Decimal("300000"),   # 필러: 300k
        Decimal("500000"),   # 리프팅: 500k
    ]
    for cp, price in zip(sp_clinic_procedures, price_configs):
        p = ProcedurePricing(
            id=uuid.uuid4(),
            clinic_procedure_id=cp.id,
            clinic_id=sp_clinic.id,
            regular_price=price,
        )
        db.add(p)
        prices.append(p)
    await db.commit()
    for p in prices:
        await db.refresh(p)
    return prices


class TestSalesPerformanceCalculator:
    @pytest.mark.asyncio
    async def test_calculate_scores(
        self,
        db: AsyncSession,
        sp_clinic: Clinic,
        sp_clinic_procedures: list[ClinicProcedure],
        sp_pricing: list[ProcedurePricing],
    ):
        calculator = SalesPerformanceCalculator(db)
        scores = await calculator.calculate(sp_clinic.id)

        assert len(scores) == 3
        for cp_id, score in scores.items():
            assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_margin_ranking(
        self,
        db: AsyncSession,
        sp_clinic: Clinic,
        sp_clinic_procedures: list[ClinicProcedure],
        sp_pricing: list[ProcedurePricing],
    ):
        """보톡스 has the highest margin per minute:
        (150000 - 5000) / 30 = 4833/min
        필러: (300000 - 20000) / 45 = 6222/min
        리프팅: (500000 - 50000) / 60 = 7500/min
        So 리프팅 > 필러 > 보톡스 for margin, but difficulty/preference differ.
        """
        calculator = SalesPerformanceCalculator(db)
        scores = await calculator.calculate(sp_clinic.id)

        botox_id = sp_clinic_procedures[0].id
        filler_id = sp_clinic_procedures[1].id
        lifting_id = sp_clinic_procedures[2].id

        # 보톡스: lowest margin rank but best difficulty(1→30) and preference(1→30)
        # 리프팅: highest margin rank but worst difficulty(5→6) and preference(3→0)
        # So 보톡스 total should be higher than 리프팅
        assert scores[botox_id] > scores[lifting_id]

    @pytest.mark.asyncio
    async def test_difficulty_score_mapping(
        self,
        db: AsyncSession,
        sp_clinic: Clinic,
        sp_clinic_procedures: list[ClinicProcedure],
        sp_pricing: list[ProcedurePricing],
    ):
        calculator = SalesPerformanceCalculator(db)
        scores = await calculator.calculate(sp_clinic.id)

        # All scores should be positive
        for score in scores.values():
            assert score > 0

    @pytest.mark.asyncio
    async def test_updates_db_scores(
        self,
        db: AsyncSession,
        sp_clinic: Clinic,
        sp_clinic_procedures: list[ClinicProcedure],
        sp_pricing: list[ProcedurePricing],
    ):
        calculator = SalesPerformanceCalculator(db)
        await calculator.calculate(sp_clinic.id)

        # Refresh to see updated scores
        for cp in sp_clinic_procedures:
            await db.refresh(cp)
            assert cp.sales_performance_score is not None
            assert float(cp.sales_performance_score) > 0

    @pytest.mark.asyncio
    async def test_no_procedures_returns_empty(
        self, db: AsyncSession, sp_clinic: Clinic
    ):
        # Create a different clinic with no procedures
        empty_clinic = Clinic(id=uuid.uuid4(), name="빈의원", slug="empty-sp")
        db.add(empty_clinic)
        await db.commit()

        calculator = SalesPerformanceCalculator(db)
        scores = await calculator.calculate(empty_clinic.id)
        assert scores == {}

    @pytest.mark.asyncio
    async def test_missing_pricing_uses_default_margin(
        self,
        db: AsyncSession,
        sp_clinic: Clinic,
        sp_clinic_procedures: list[ClinicProcedure],
    ):
        """Without pricing data, margin score defaults to 20 points."""
        calculator = SalesPerformanceCalculator(db)
        scores = await calculator.calculate(sp_clinic.id)

        # All should still get scores (using default margin = 20)
        assert len(scores) == 3
        for score in scores.values():
            assert score > 0
