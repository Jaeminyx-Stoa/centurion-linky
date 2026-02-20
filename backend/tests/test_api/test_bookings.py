import uuid
from datetime import date, time

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def bk_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="예약의원", slug="bk-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def bk_admin(db: AsyncSession, bk_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=bk_clinic.id,
        email="bk-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="예약관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def bk_token(client: AsyncClient, bk_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bk-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def bk_headers(bk_token: str) -> dict:
    return {"Authorization": f"Bearer {bk_token}"}


@pytest_asyncio.fixture
async def bk_customer(db: AsyncSession, bk_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=bk_clinic.id,
        messenger_type="telegram",
        messenger_user_id="bk-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def bk_booking(
    db: AsyncSession, bk_clinic: Clinic, bk_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=bk_clinic.id,
        customer_id=bk_customer.id,
        booking_date=date(2026, 3, 15),
        booking_time=time(14, 0),
        status="pending",
        total_amount=500000,
        currency="KRW",
        deposit_amount=100000,
        remaining_amount=400000,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def bk_confirmed_booking(
    db: AsyncSession, bk_clinic: Clinic, bk_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=bk_clinic.id,
        customer_id=bk_customer.id,
        booking_date=date(2026, 3, 20),
        booking_time=time(10, 0),
        status="confirmed",
        total_amount=300000,
        currency="KRW",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


# --- Tests ---
class TestCreateBooking:
    @pytest.mark.asyncio
    async def test_create_basic(
        self, client: AsyncClient, bk_headers: dict, bk_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": str(bk_customer.id),
                "booking_date": "2026-04-01",
                "booking_time": "10:00:00",
            },
            headers=bk_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["customer_id"] == str(bk_customer.id)
        assert data["booking_date"] == "2026-04-01"

    @pytest.mark.asyncio
    async def test_create_with_amounts(
        self, client: AsyncClient, bk_headers: dict, bk_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": str(bk_customer.id),
                "booking_date": "2026-04-02",
                "booking_time": "14:30:00",
                "total_amount": "500000",
                "deposit_amount": "100000",
            },
            headers=bk_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["total_amount"]) == 500000
        assert float(data["deposit_amount"]) == 100000
        assert float(data["remaining_amount"]) == 400000

    @pytest.mark.asyncio
    async def test_create_without_deposit(
        self, client: AsyncClient, bk_headers: dict, bk_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": str(bk_customer.id),
                "booking_date": "2026-04-03",
                "booking_time": "09:00:00",
                "total_amount": "200000",
            },
            headers=bk_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["remaining_amount"] is None


class TestListBookings:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.get("/api/v1/bookings", headers=bk_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert "limit" in data
        assert "offset" in data

    @pytest.mark.asyncio
    async def test_list_filter_by_status(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.get(
            "/api/v1/bookings?status=pending", headers=bk_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(b["status"] == "pending" for b in data["items"])

    @pytest.mark.asyncio
    async def test_list_filter_no_results(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.get(
            "/api/v1/bookings?status=no_show", headers=bk_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestGetBooking:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.get(
            f"/api/v1/bookings/{bk_booking.id}", headers=bk_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(bk_booking.id)

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, bk_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/bookings/{uuid.uuid4()}", headers=bk_headers
        )
        assert resp.status_code == 404


class TestUpdateBooking:
    @pytest.mark.asyncio
    async def test_update_date(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.patch(
            f"/api/v1/bookings/{bk_booking.id}",
            json={"booking_date": "2026-04-10"},
            headers=bk_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["booking_date"] == "2026-04-10"

    @pytest.mark.asyncio
    async def test_update_amounts_recalculates_remaining(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.patch(
            f"/api/v1/bookings/{bk_booking.id}",
            json={"deposit_amount": "200000"},
            headers=bk_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # total=500000, deposit=200000 → remaining=300000
        assert float(data["remaining_amount"]) == 300000


class TestCancelBooking:
    @pytest.mark.asyncio
    async def test_cancel_pending(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.post(
            f"/api/v1/bookings/{bk_booking.id}/cancel",
            json={"cancellation_reason": "고객 요청"},
            headers=bk_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] == "고객 요청"

    @pytest.mark.asyncio
    async def test_cancel_without_reason(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.post(
            f"/api/v1/bookings/{bk_booking.id}/cancel",
            headers=bk_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_already_completed_fails(
        self,
        client: AsyncClient,
        bk_headers: dict,
        bk_confirmed_booking: Booking,
        db: AsyncSession,
    ):
        # Manually set to completed
        bk_confirmed_booking.status = "completed"
        await db.commit()

        resp = await client.post(
            f"/api/v1/bookings/{bk_confirmed_booking.id}/cancel",
            headers=bk_headers,
        )
        assert resp.status_code == 400


class TestCompleteBooking:
    @pytest.mark.asyncio
    async def test_complete_confirmed(
        self,
        client: AsyncClient,
        bk_headers: dict,
        bk_confirmed_booking: Booking,
    ):
        resp = await client.post(
            f"/api/v1/bookings/{bk_confirmed_booking.id}/complete",
            headers=bk_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_complete_pending_fails(
        self, client: AsyncClient, bk_headers: dict, bk_booking: Booking
    ):
        resp = await client.post(
            f"/api/v1/bookings/{bk_booking.id}/complete",
            headers=bk_headers,
        )
        assert resp.status_code == 400
