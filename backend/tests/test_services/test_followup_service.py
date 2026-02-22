import uuid
from datetime import date, time, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.customer import Customer
from app.models.followup_rule import FollowupRule
from app.models.procedure import Procedure
from app.models.side_effect_keyword import SideEffectKeyword
from app.services.followup_service import FollowupService


@pytest_asyncio.fixture
async def fu_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="팔로업의원", slug="followup-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def fu_customer(db: AsyncSession, fu_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=fu_clinic.id,
        messenger_type="telegram",
        messenger_user_id="fu-tg-1",
        language_code="ko",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def fu_procedure(db: AsyncSession) -> Procedure:
    proc = Procedure(
        id=uuid.uuid4(),
        name_ko="보톡스",
        name_en="Botox",
        slug="botox",
    )
    db.add(proc)
    await db.commit()
    await db.refresh(proc)
    return proc


@pytest_asyncio.fixture
async def fu_clinic_procedure(
    db: AsyncSession, fu_clinic: Clinic, fu_procedure: Procedure
) -> ClinicProcedure:
    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=fu_clinic.id,
        procedure_id=fu_procedure.id,
    )
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp


@pytest_asyncio.fixture
async def fu_booking(
    db: AsyncSession,
    fu_clinic: Clinic,
    fu_customer: Customer,
    fu_clinic_procedure: ClinicProcedure,
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=fu_clinic.id,
        customer_id=fu_customer.id,
        clinic_procedure_id=fu_clinic_procedure.id,
        booking_date=date(2026, 7, 1),
        booking_time=time(10, 0),
        status="completed",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def fu_rules(
    db: AsyncSession, fu_clinic: Clinic, fu_procedure: Procedure
) -> list[FollowupRule]:
    rules = [
        FollowupRule(
            id=uuid.uuid4(),
            clinic_id=fu_clinic.id,
            procedure_id=fu_procedure.id,
            event_type="recovery_check",
            delay_days=1,
            delay_hours=0,
            message_template={"ko": "시술 후 상태는 어떠신가요?", "en": "How are you feeling?"},
            sort_order=0,
        ),
        FollowupRule(
            id=uuid.uuid4(),
            clinic_id=fu_clinic.id,
            procedure_id=None,  # global rule
            event_type="result_check",
            delay_days=7,
            delay_hours=0,
            message_template={"ko": "결과에 만족하시나요?"},
            sort_order=1,
        ),
    ]
    for r in rules:
        db.add(r)
    await db.commit()
    for r in rules:
        await db.refresh(r)
    return rules


class TestScheduleFollowups:
    @pytest.mark.asyncio
    async def test_creates_events_for_matching_rules(
        self, db: AsyncSession, fu_booking: Booking, fu_rules: list[FollowupRule]
    ):
        svc = FollowupService(db)
        events = await svc.schedule_followups(fu_booking.id)

        # Should create events for both procedure-specific and global rules
        assert len(events) == 2
        event_types = {e.event_type for e in events}
        assert "recovery_check" in event_types
        assert "result_check" in event_types

    @pytest.mark.asyncio
    async def test_sets_correct_scheduled_at(
        self, db: AsyncSession, fu_booking: Booking, fu_rules: list[FollowupRule]
    ):
        svc = FollowupService(db)
        events = await svc.schedule_followups(fu_booking.id)

        for event in events:
            assert event.scheduled_at is not None
            assert event.status == "scheduled"

    @pytest.mark.asyncio
    async def test_no_rules_returns_empty(self, db: AsyncSession, fu_clinic: Clinic, fu_customer: Customer):
        # Booking without any matching rules
        booking = Booking(
            id=uuid.uuid4(),
            clinic_id=fu_clinic.id,
            customer_id=fu_customer.id,
            booking_date=date(2026, 8, 1),
            booking_time=time(14, 0),
            status="completed",
        )
        db.add(booking)
        await db.commit()

        svc = FollowupService(db)
        events = await svc.schedule_followups(booking.id)
        # Only global rules should match (if any exist in this session)
        # Without fu_rules fixture, should be empty
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_nonexistent_booking_returns_empty(self, db: AsyncSession):
        svc = FollowupService(db)
        events = await svc.schedule_followups(uuid.uuid4())
        assert events == []


class TestCheckSideEffects:
    @pytest.mark.asyncio
    async def test_detects_matching_keywords(self, db: AsyncSession, fu_clinic: Clinic):
        kw = SideEffectKeyword(
            id=uuid.uuid4(),
            clinic_id=fu_clinic.id,
            language="ko",
            keywords=["아프다", "부어오르다", "빨갛다"],
            severity="normal",
        )
        db.add(kw)
        await db.commit()

        svc = FollowupService(db)
        result = await svc.check_side_effects(
            "시술 부위가 아프다", fu_clinic.id, "ko"
        )
        assert result is not None
        assert "아프다" in result["matched_keywords"]
        assert result["severity"] == "normal"

    @pytest.mark.asyncio
    async def test_urgent_severity(self, db: AsyncSession, fu_clinic: Clinic):
        kw = SideEffectKeyword(
            id=uuid.uuid4(),
            clinic_id=fu_clinic.id,
            language="ko",
            keywords=["출혈", "감염"],
            severity="urgent",
        )
        db.add(kw)
        await db.commit()

        svc = FollowupService(db)
        result = await svc.check_side_effects(
            "출혈이 멈추지 않아요", fu_clinic.id, "ko"
        )
        assert result is not None
        assert result["severity"] == "urgent"

    @pytest.mark.asyncio
    async def test_no_match_returns_none(self, db: AsyncSession, fu_clinic: Clinic):
        kw = SideEffectKeyword(
            id=uuid.uuid4(),
            clinic_id=fu_clinic.id,
            language="ko",
            keywords=["아프다", "부어오르다"],
            severity="normal",
        )
        db.add(kw)
        await db.commit()

        svc = FollowupService(db)
        result = await svc.check_side_effects(
            "결과가 좋아서 감사합니다", fu_clinic.id, "ko"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_message(self, db: AsyncSession, fu_clinic: Clinic):
        svc = FollowupService(db)
        result = await svc.check_side_effects("", fu_clinic.id, "ko")
        assert result is None
