"""Tests for consultation agent tools."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.tools import create_consultation_tools
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount
from app.models.procedure import Procedure


@pytest.fixture
async def clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid.uuid4(),
        name="에이전트테스트의원",
        slug="test-agent-tools",
        phone="02-1234-5678",
        address="서울시 강남구",
        email="test@clinic.com",
    )
    db.add(clinic)
    await db.flush()
    return clinic


@pytest.fixture
async def customer(db: AsyncSession, clinic: Clinic) -> Customer:
    c = Customer(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        messenger_user_id="test_user_123",
        messenger_type="telegram",
        name="테스트고객",
        language_code="ko",
        country_code="KR",
    )
    db.add(c)
    await db.flush()
    return c


@pytest.fixture
async def messenger_account(db: AsyncSession, clinic: Clinic) -> MessengerAccount:
    ma = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        messenger_type="telegram",
        account_id="bot_123",
        account_name="TestBot",
        access_token="test_token",
    )
    db.add(ma)
    await db.flush()
    return ma


@pytest.fixture
async def conversation(
    db: AsyncSession, clinic: Clinic, customer: Customer, messenger_account: MessengerAccount
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        customer_id=customer.id,
        messenger_account_id=messenger_account.id,
        status="active",
        ai_mode=True,
    )
    db.add(conv)
    await db.flush()
    return conv


@pytest.fixture
async def procedure_with_clinic(db: AsyncSession, clinic: Clinic) -> ClinicProcedure:
    proc = Procedure(
        id=uuid.uuid4(),
        name_ko="보톡스",
        name_en="Botox",
        slug="botox-agent-test",
        description_ko="주름 개선 시술",
        duration_minutes=20,
    )
    db.add(proc)
    await db.flush()

    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        procedure_id=proc.id,
        is_active=True,
    )
    db.add(cp)
    await db.flush()
    return cp


@pytest.fixture
def tools(db, clinic, customer, conversation):
    return create_consultation_tools(db, clinic.id, customer.id, conversation.id)


@pytest.mark.asyncio
async def test_check_availability(tools):
    """check_availability should return time slots for a valid date."""
    check_avail = tools[3]  # check_availability
    result = await check_avail.ainvoke({"check_date": "2026-03-15"})
    assert "10:00" in result
    assert "17:00" in result


@pytest.mark.asyncio
async def test_check_availability_invalid_date(tools):
    """check_availability should handle invalid date format."""
    check_avail = tools[3]
    result = await check_avail.ainvoke({"check_date": "invalid"})
    assert "올바르지 않습니다" in result


@pytest.mark.asyncio
async def test_get_clinic_info(db: AsyncSession, tools, clinic):
    """get_clinic_info should return clinic details."""
    get_info = tools[5]  # get_clinic_info
    result = await get_info.ainvoke({})
    assert "에이전트테스트의원" in result
    assert "서울시 강남구" in result
    assert "02-1234-5678" in result


@pytest.mark.asyncio
async def test_escalate_to_human(db: AsyncSession, tools, conversation):
    """escalate_to_human should set ai_mode=False."""
    escalate = tools[4]  # escalate_to_human
    result = await escalate.ainvoke({"reason": "고객 요청"})
    assert "상담사 연결 중" in result

    await db.refresh(conversation)
    assert conversation.ai_mode is False
    assert conversation.status == "waiting"


@pytest.mark.asyncio
async def test_create_booking_success(
    db: AsyncSession, tools, procedure_with_clinic
):
    """create_booking should create a booking record."""
    create_book = tools[1]  # create_booking
    result = await create_book.ainvoke({
        "procedure_name": "보톡스",
        "booking_date": "2026-03-20",
        "booking_time": "14:00",
    })
    assert "예약이 완료되었습니다" in result
    assert "보톡스" in result


@pytest.mark.asyncio
async def test_create_booking_procedure_not_found(tools):
    """create_booking should handle missing procedure."""
    create_book = tools[1]
    result = await create_book.ainvoke({
        "procedure_name": "존재하지않는시술",
        "booking_date": "2026-03-20",
        "booking_time": "14:00",
    })
    assert "찾을 수 없습니다" in result
