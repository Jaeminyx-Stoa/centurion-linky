import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.crm_event import CRMEvent
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.satisfaction_survey import SatisfactionSurvey
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def crm_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="CRM의원", slug="crm-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def crm_admin(db: AsyncSession, crm_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        email="crm-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="CRM관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def crm_token(client: AsyncClient, crm_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "crm-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def crm_headers(crm_token: str) -> dict:
    return {"Authorization": f"Bearer {crm_token}"}


@pytest_asyncio.fixture
async def crm_customer(db: AsyncSession, crm_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        messenger_type="telegram",
        messenger_user_id="crm-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def crm_booking(
    db: AsyncSession, crm_clinic: Clinic, crm_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        customer_id=crm_customer.id,
        booking_date=date(2026, 7, 1),
        booking_time=time(10, 0),
        status="confirmed",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def crm_payment(
    db: AsyncSession, crm_clinic: Clinic, crm_customer: Customer, crm_booking: Booking
) -> Payment:
    payment = Payment(
        id=uuid.uuid4(),
        clinic_id=crm_clinic.id,
        booking_id=crm_booking.id,
        customer_id=crm_customer.id,
        payment_type="deposit",
        amount=100000,
        currency="KRW",
        status="completed",
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


def _make_crm_event(
    clinic: Clinic,
    customer: Customer,
    event_type: str = "receipt",
    status: str = "scheduled",
    offset_hours: int = 0,
    booking: Booking | None = None,
    payment: Payment | None = None,
) -> CRMEvent:
    return CRMEvent(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        customer_id=customer.id,
        booking_id=booking.id if booking else None,
        payment_id=payment.id if payment else None,
        event_type=event_type,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=offset_hours),
        status=status,
    )


@pytest_asyncio.fixture
async def crm_events(
    db: AsyncSession,
    crm_clinic: Clinic,
    crm_customer: Customer,
    crm_booking: Booking,
    crm_payment: Payment,
) -> list[CRMEvent]:
    events = [
        _make_crm_event(crm_clinic, crm_customer, "receipt", "sent", 0, crm_booking, crm_payment),
        _make_crm_event(crm_clinic, crm_customer, "aftercare", "scheduled", 3, crm_booking, crm_payment),
        _make_crm_event(crm_clinic, crm_customer, "survey_1", "scheduled", 6, crm_booking, crm_payment),
        _make_crm_event(crm_clinic, crm_customer, "survey_2", "cancelled", 168, crm_booking, crm_payment),
    ]
    for e in events:
        db.add(e)
    await db.commit()
    for e in events:
        await db.refresh(e)
    return events


# --- CRM Events Tests ---
class TestListEvents:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, crm_headers: dict, crm_events: list[CRMEvent]
    ):
        resp = await client.get("/api/v1/crm/events", headers=crm_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, client: AsyncClient, crm_headers: dict, crm_events: list[CRMEvent]
    ):
        resp = await client.get(
            "/api/v1/crm/events?status=scheduled", headers=crm_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(e["status"] == "scheduled" for e in data["items"])
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_filter_by_event_type(
        self, client: AsyncClient, crm_headers: dict, crm_events: list[CRMEvent]
    ):
        resp = await client.get(
            "/api/v1/crm/events?event_type=receipt", headers=crm_headers
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, crm_headers: dict, crm_events: list[CRMEvent]
    ):
        resp = await client.get(
            f"/api/v1/crm/events/{crm_events[0].id}", headers=crm_headers
        )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "receipt"

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, crm_headers: dict):
        resp = await client.get(
            f"/api/v1/crm/events/{uuid.uuid4()}", headers=crm_headers
        )
        assert resp.status_code == 404


class TestCancelEvent:
    @pytest.mark.asyncio
    async def test_cancel_scheduled(
        self, client: AsyncClient, crm_headers: dict, crm_events: list[CRMEvent]
    ):
        # crm_events[1] is "aftercare" with status "scheduled"
        resp = await client.post(
            f"/api/v1/crm/events/{crm_events[1].id}/cancel", headers=crm_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_already_sent_fails(
        self, client: AsyncClient, crm_headers: dict, crm_events: list[CRMEvent]
    ):
        # crm_events[0] is "receipt" with status "sent"
        resp = await client.post(
            f"/api/v1/crm/events/{crm_events[0].id}/cancel", headers=crm_headers
        )
        assert resp.status_code == 400


# --- Surveys Tests ---
class TestCreateSurvey:
    @pytest.mark.asyncio
    async def test_create_round1(
        self, client: AsyncClient, crm_headers: dict, crm_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/crm/surveys",
            json={
                "customer_id": str(crm_customer.id),
                "survey_round": 1,
                "satisfaction_score": 4,
                "feedback_text": "좋았습니다",
            },
            headers=crm_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["survey_round"] == 1
        assert data["satisfaction_score"] == 4
        assert data["responded_at"] is not None

    @pytest.mark.asyncio
    async def test_create_round3_with_nps(
        self, client: AsyncClient, crm_headers: dict, crm_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/crm/surveys",
            json={
                "customer_id": str(crm_customer.id),
                "survey_round": 3,
                "satisfaction_score": 5,
                "nps_score": 9,
            },
            headers=crm_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["nps_score"] == 9


class TestListSurveys:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, crm_headers: dict, crm_customer: Customer
    ):
        # Create a survey first
        await client.post(
            "/api/v1/crm/surveys",
            json={
                "customer_id": str(crm_customer.id),
                "survey_round": 1,
                "satisfaction_score": 4,
            },
            headers=crm_headers,
        )
        resp = await client.get("/api/v1/crm/surveys", headers=crm_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_round(
        self, client: AsyncClient, crm_headers: dict, crm_customer: Customer
    ):
        await client.post(
            "/api/v1/crm/surveys",
            json={
                "customer_id": str(crm_customer.id),
                "survey_round": 2,
                "satisfaction_score": 3,
                "revisit_intention": "yes",
            },
            headers=crm_headers,
        )
        resp = await client.get(
            "/api/v1/crm/surveys?survey_round=2", headers=crm_headers
        )
        assert resp.status_code == 200
        assert all(s["survey_round"] == 2 for s in resp.json()["items"])


# --- Survey Summary ---
@pytest_asyncio.fixture
async def survey_data(
    db: AsyncSession, crm_clinic: Clinic, crm_customer: Customer
) -> list[SatisfactionSurvey]:
    surveys = [
        SatisfactionSurvey(
            id=uuid.uuid4(),
            clinic_id=crm_clinic.id,
            customer_id=crm_customer.id,
            survey_round=1,
            satisfaction_score=4,
            responded_at=datetime.now(timezone.utc),
        ),
        SatisfactionSurvey(
            id=uuid.uuid4(),
            clinic_id=crm_clinic.id,
            customer_id=crm_customer.id,
            survey_round=2,
            satisfaction_score=5,
            revisit_intention="yes",
            responded_at=datetime.now(timezone.utc),
        ),
        SatisfactionSurvey(
            id=uuid.uuid4(),
            clinic_id=crm_clinic.id,
            customer_id=crm_customer.id,
            survey_round=3,
            satisfaction_score=5,
            nps_score=9,
            revisit_intention="yes",
            responded_at=datetime.now(timezone.utc),
        ),
        SatisfactionSurvey(
            id=uuid.uuid4(),
            clinic_id=crm_clinic.id,
            customer_id=crm_customer.id,
            survey_round=3,
            satisfaction_score=3,
            nps_score=6,
            revisit_intention="maybe",
            responded_at=datetime.now(timezone.utc),
        ),
    ]
    for s in surveys:
        db.add(s)
    await db.commit()
    for s in surveys:
        await db.refresh(s)
    return surveys


class TestSurveySummary:
    @pytest.mark.asyncio
    async def test_summary(
        self,
        client: AsyncClient,
        crm_headers: dict,
        survey_data: list[SatisfactionSurvey],
    ):
        resp = await client.get(
            "/api/v1/crm/surveys/summary", headers=crm_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_surveys"] == 4
        assert data["avg_satisfaction"] is not None
        assert data["by_round"]["1"]["count"] == 1
        assert data["by_round"]["3"]["count"] == 2

    @pytest.mark.asyncio
    async def test_summary_empty(self, client: AsyncClient, crm_headers: dict):
        resp = await client.get(
            "/api/v1/crm/surveys/summary", headers=crm_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_surveys"] == 0
        assert data["avg_satisfaction"] is None


# --- Dashboard ---
class TestDashboard:
    @pytest.mark.asyncio
    async def test_dashboard(
        self,
        client: AsyncClient,
        crm_headers: dict,
        crm_events: list[CRMEvent],
        survey_data: list[SatisfactionSurvey],
    ):
        resp = await client.get("/api/v1/crm/dashboard", headers=crm_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 4
        assert data["sent"] == 1
        assert data["scheduled"] == 2
        assert data["cancelled"] == 1
        assert data["total_surveys"] == 4
        assert data["avg_satisfaction"] is not None

    @pytest.mark.asyncio
    async def test_dashboard_empty(self, client: AsyncClient, crm_headers: dict):
        resp = await client.get("/api/v1/crm/dashboard", headers=crm_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 0
        assert data["total_surveys"] == 0


# --- Satisfaction Trend ---
class TestSatisfactionTrend:
    @pytest.mark.asyncio
    async def test_trend(
        self,
        client: AsyncClient,
        crm_headers: dict,
        survey_data: list[SatisfactionSurvey],
    ):
        resp = await client.get(
            "/api/v1/crm/satisfaction-trend", headers=crm_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3  # rounds 1, 2, 3


# --- NPS ---
class TestNPS:
    @pytest.mark.asyncio
    async def test_nps_stats(
        self,
        client: AsyncClient,
        crm_headers: dict,
        survey_data: list[SatisfactionSurvey],
    ):
        resp = await client.get("/api/v1/crm/nps", headers=crm_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2  # 2 surveys with nps_score
        assert data["promoters"] == 1  # score 9
        assert data["detractors"] == 1  # score 6
        assert data["nps"] == 0.0  # (1-1)/2*100 = 0

    @pytest.mark.asyncio
    async def test_nps_empty(self, client: AsyncClient, crm_headers: dict):
        resp = await client.get("/api/v1/crm/nps", headers=crm_headers)
        assert resp.status_code == 200
        assert resp.json()["nps"] is None


# --- Revisit Rate ---
class TestRevisitRate:
    @pytest.mark.asyncio
    async def test_revisit_rate(
        self,
        client: AsyncClient,
        crm_headers: dict,
        survey_data: list[SatisfactionSurvey],
    ):
        resp = await client.get("/api/v1/crm/revisit-rate", headers=crm_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3  # 3 surveys with revisit_intention
        assert data["yes"] == 2
        assert data["maybe"] == 1

    @pytest.mark.asyncio
    async def test_revisit_empty(self, client: AsyncClient, crm_headers: dict):
        resp = await client.get("/api/v1/crm/revisit-rate", headers=crm_headers)
        assert resp.status_code == 200
        assert resp.json()["yes_rate"] is None
