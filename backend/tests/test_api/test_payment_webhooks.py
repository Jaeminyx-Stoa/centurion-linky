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
async def wh_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="웹훅의원", slug="wh-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def wh_admin(db: AsyncSession, wh_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=wh_clinic.id,
        email="wh-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="웹훅관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def wh_token(client: AsyncClient, wh_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wh-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def wh_headers(wh_token: str) -> dict:
    return {"Authorization": f"Bearer {wh_token}"}


@pytest_asyncio.fixture
async def wh_customer(db: AsyncSession, wh_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=wh_clinic.id,
        messenger_type="telegram",
        messenger_user_id="wh-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def wh_booking(
    db: AsyncSession, wh_clinic: Clinic, wh_customer: Customer
) -> Booking:
    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=wh_clinic.id,
        customer_id=wh_customer.id,
        booking_date=date(2026, 6, 1),
        booking_time=time(10, 0),
        status="pending",
        total_amount=Decimal("500000"),
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


def _make_payment(
    clinic: Clinic,
    customer: Customer,
    booking: Booking,
    pg_provider: str,
    pg_payment_id: str,
) -> Payment:
    return Payment(
        id=uuid.uuid4(),
        clinic_id=clinic.id,
        booking_id=booking.id,
        customer_id=customer.id,
        payment_type="deposit",
        amount=Decimal("100000"),
        currency="KRW",
        pg_provider=pg_provider,
        pg_payment_id=pg_payment_id,
        status="link_sent",
        payment_link=f"https://pay.example.com/{pg_payment_id}",
    )


# --- Webhook Tests ---
class TestKingOrderWebhook:
    @pytest.mark.asyncio
    async def test_successful_webhook(
        self,
        client: AsyncClient,
        db: AsyncSession,
        wh_clinic: Clinic,
        wh_customer: Customer,
        wh_booking: Booking,
    ):
        payment = _make_payment(
            wh_clinic, wh_customer, wh_booking, "kingorder", "ko_test_001"
        )
        db.add(payment)
        await db.commit()

        resp = await client.post(
            "/api/webhooks/payments/kingorder",
            json={
                "payment_id": "ko_test_001",
                "status": "completed",
                "amount": 100000,
                "currency": "KRW",
                "payment_method": "card",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_confirms_booking(
        self,
        client: AsyncClient,
        db: AsyncSession,
        wh_clinic: Clinic,
        wh_customer: Customer,
        wh_booking: Booking,
    ):
        payment = _make_payment(
            wh_clinic, wh_customer, wh_booking, "kingorder", "ko_test_002"
        )
        db.add(payment)
        await db.commit()

        await client.post(
            "/api/webhooks/payments/kingorder",
            json={
                "payment_id": "ko_test_002",
                "status": "completed",
                "amount": 100000,
                "currency": "KRW",
            },
        )

        await db.refresh(wh_booking)
        assert wh_booking.status == "confirmed"

    @pytest.mark.asyncio
    async def test_not_found_payment(self, client: AsyncClient):
        resp = await client.post(
            "/api/webhooks/payments/kingorder",
            json={
                "payment_id": "ko_nonexistent",
                "status": "completed",
                "amount": 100000,
                "currency": "KRW",
            },
        )
        assert resp.status_code == 404


class TestAlipayWebhook:
    @pytest.mark.asyncio
    async def test_successful_webhook(
        self,
        client: AsyncClient,
        db: AsyncSession,
        wh_clinic: Clinic,
        wh_customer: Customer,
        wh_booking: Booking,
    ):
        payment = _make_payment(
            wh_clinic, wh_customer, wh_booking, "alipay", "ali_test_001"
        )
        db.add(payment)
        await db.commit()

        resp = await client.post(
            "/api/webhooks/payments/alipay",
            json={
                "payment_id": "ali_test_001",
                "status": "completed",
                "amount": 100000,
                "currency": "CNY",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/webhooks/payments/alipay",
            json={
                "payment_id": "ali_nonexistent",
                "status": "completed",
                "amount": 100000,
            },
        )
        assert resp.status_code == 404


class TestStripeWebhook:
    @pytest.mark.asyncio
    async def test_successful_webhook(
        self,
        client: AsyncClient,
        db: AsyncSession,
        wh_clinic: Clinic,
        wh_customer: Customer,
        wh_booking: Booking,
    ):
        payment = _make_payment(
            wh_clinic, wh_customer, wh_booking, "stripe", "pi_test_001"
        )
        db.add(payment)
        await db.commit()

        resp = await client.post(
            "/api/webhooks/payments/stripe",
            json={
                "payment_id": "pi_test_001",
                "status": "completed",
                "amount": 50000,
                "currency": "USD",
                "payment_method": "card",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/webhooks/payments/stripe",
            json={
                "payment_id": "pi_nonexistent",
                "status": "completed",
                "amount": 50000,
            },
        )
        assert resp.status_code == 404


# --- Payment Settings Tests ---
class TestPaymentSettings:
    @pytest.mark.asyncio
    async def test_get_empty_settings(
        self, client: AsyncClient, wh_headers: dict
    ):
        resp = await client.get(
            "/api/v1/payment-settings", headers=wh_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_and_read(
        self, client: AsyncClient, wh_headers: dict
    ):
        # Update
        resp = await client.patch(
            "/api/v1/payment-settings",
            json={
                "default_provider": "kingorder",
                "default_currency": "KRW",
                "deposit_required": True,
                "deposit_percentage": 20.0,
            },
            headers=wh_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_provider"] == "kingorder"
        assert data["deposit_required"] is True

        # Read back
        resp = await client.get(
            "/api/v1/payment-settings", headers=wh_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["default_currency"] == "KRW"
        assert data["deposit_percentage"] == 20.0
