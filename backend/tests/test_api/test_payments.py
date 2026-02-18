import uuid
from datetime import date, time
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def pay_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="결제의원", slug="pay-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def pay_admin(db: AsyncSession, pay_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=pay_clinic.id,
        email="pay-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="결제관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def pay_token(client: AsyncClient, pay_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "pay-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def pay_headers(pay_token: str) -> dict:
    return {"Authorization": f"Bearer {pay_token}"}


@pytest_asyncio.fixture
async def pay_customer(db: AsyncSession, pay_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=pay_clinic.id,
        messenger_type="telegram",
        messenger_user_id="pay-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def pay_booking(
    db: AsyncSession, pay_clinic: Clinic, pay_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=pay_clinic.id,
        customer_id=pay_customer.id,
        booking_date=date(2026, 4, 1),
        booking_time=time(10, 0),
        status="pending",
        total_amount=Decimal("500000"),
        currency="KRW",
        deposit_amount=Decimal("100000"),
        remaining_amount=Decimal("400000"),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def pay_confirmed_booking(
    db: AsyncSession, pay_clinic: Clinic, pay_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=pay_clinic.id,
        customer_id=pay_customer.id,
        booking_date=date(2026, 4, 5),
        booking_time=time(14, 0),
        status="confirmed",
        total_amount=Decimal("300000"),
        currency="KRW",
        deposit_amount=Decimal("100000"),
        remaining_amount=Decimal("200000"),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@pytest_asyncio.fixture
async def pay_payment(
    db: AsyncSession, pay_clinic: Clinic, pay_customer: Customer, pay_booking: Booking
) -> Payment:
    payment = Payment(
        id=uuid.uuid4(),
        clinic_id=pay_clinic.id,
        booking_id=pay_booking.id,
        customer_id=pay_customer.id,
        payment_type="deposit",
        amount=Decimal("100000"),
        currency="KRW",
        pg_provider="stub",
        pg_payment_id="stub_existing_123",
        status="link_sent",
        payment_link="https://pay.stub.dev/stub_existing_123",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


# --- Tests ---
class TestCreatePaymentLink:
    @pytest.mark.asyncio
    async def test_create_link_basic(
        self, client: AsyncClient, pay_headers: dict, pay_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/payments/create-link",
            json={
                "customer_id": str(pay_customer.id),
                "payment_type": "deposit",
                "amount": "100000",
                "currency": "KRW",
            },
            headers=pay_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "link_sent"
        assert data["payment_link"] is not None
        assert data["payment_type"] == "deposit"

    @pytest.mark.asyncio
    async def test_create_link_with_booking(
        self,
        client: AsyncClient,
        pay_headers: dict,
        pay_customer: Customer,
        pay_booking: Booking,
    ):
        resp = await client.post(
            "/api/v1/payments/create-link",
            json={
                "booking_id": str(pay_booking.id),
                "customer_id": str(pay_customer.id),
                "payment_type": "deposit",
                "amount": "100000",
            },
            headers=pay_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["booking_id"] == str(pay_booking.id)

    @pytest.mark.asyncio
    async def test_create_link_with_provider_override(
        self, client: AsyncClient, pay_headers: dict, pay_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/payments/create-link",
            json={
                "customer_id": str(pay_customer.id),
                "payment_type": "full",
                "amount": "50000",
                "pg_provider": "stub",
            },
            headers=pay_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["pg_provider"] == "stub"
        assert "stub" in data["pg_payment_id"]


class TestRequestRemaining:
    @pytest.mark.asyncio
    async def test_request_remaining_success(
        self,
        client: AsyncClient,
        pay_headers: dict,
        pay_customer: Customer,
        pay_confirmed_booking: Booking,
    ):
        resp = await client.post(
            "/api/v1/payments/request-remaining",
            json={
                "booking_id": str(pay_confirmed_booking.id),
                "customer_id": str(pay_customer.id),
                "amount": "200000",
            },
            headers=pay_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["payment_type"] == "remaining"


class TestListPayments:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, pay_headers: dict, pay_payment: Payment
    ):
        resp = await client.get("/api/v1/payments", headers=pay_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_list_filter_by_booking(
        self,
        client: AsyncClient,
        pay_headers: dict,
        pay_payment: Payment,
        pay_booking: Booking,
    ):
        resp = await client.get(
            f"/api/v1/payments?booking_id={pay_booking.id}",
            headers=pay_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(p["booking_id"] == str(pay_booking.id) for p in data)


class TestGetPayment:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, pay_headers: dict, pay_payment: Payment
    ):
        resp = await client.get(
            f"/api/v1/payments/{pay_payment.id}", headers=pay_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(pay_payment.id)

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, pay_headers: dict):
        resp = await client.get(
            f"/api/v1/payments/{uuid.uuid4()}", headers=pay_headers
        )
        assert resp.status_code == 404


class TestPaymentStatus:
    @pytest.mark.asyncio
    async def test_status_endpoint(
        self, client: AsyncClient, pay_headers: dict, pay_payment: Payment
    ):
        resp = await client.get(
            f"/api/v1/payments/{pay_payment.id}/status",
            headers=pay_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(pay_payment.id)
        assert data["status"] == "link_sent"

    @pytest.mark.asyncio
    async def test_status_not_found(self, client: AsyncClient, pay_headers: dict):
        resp = await client.get(
            f"/api/v1/payments/{uuid.uuid4()}/status",
            headers=pay_headers,
        )
        assert resp.status_code == 404


class TestValidation:
    @pytest.mark.asyncio
    async def test_amount_must_be_positive(
        self, client: AsyncClient, pay_headers: dict, pay_customer: Customer
    ):
        resp = await client.post(
            "/api/v1/payments/create-link",
            json={
                "customer_id": str(pay_customer.id),
                "payment_type": "deposit",
                "amount": "0",
            },
            headers=pay_headers,
        )
        assert resp.status_code == 422
