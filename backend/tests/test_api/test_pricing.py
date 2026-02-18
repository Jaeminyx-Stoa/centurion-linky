import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.procedure import Procedure
from app.models.procedure_category import ProcedureCategory
from app.models.procedure_pricing import ProcedurePricing
from app.models.user import User
from app.services.pricing_service import calculate_discount


# --- Unit tests for pricing service ---
class TestCalculateDiscount:
    def test_normal_discount(self):
        rate, warning = calculate_discount(Decimal("100000"), Decimal("80000"))
        assert rate == Decimal("20.00")
        assert warning is False

    def test_exactly_49_percent(self):
        rate, warning = calculate_discount(Decimal("100000"), Decimal("51000"))
        assert rate == Decimal("49.00")
        assert warning is False

    def test_over_49_percent_triggers_warning(self):
        rate, warning = calculate_discount(Decimal("100000"), Decimal("50000"))
        assert rate == Decimal("50.00")
        assert warning is True

    def test_no_event_price(self):
        rate, warning = calculate_discount(Decimal("100000"), None)
        assert rate is None
        assert warning is False

    def test_zero_regular_price(self):
        rate, warning = calculate_discount(Decimal("0"), Decimal("50000"))
        assert rate is None
        assert warning is False


# --- Integration tests for pricing API ---
@pytest_asyncio.fixture
async def pr_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="수가의원", slug="pr-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def pr_admin(db: AsyncSession, pr_clinic: Clinic) -> User:
    from app.core.security import hash_password

    user = User(
        id=uuid.uuid4(),
        clinic_id=pr_clinic.id,
        email="pr-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="수가관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def pr_token(client: AsyncClient, pr_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "pr-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def auth_headers(pr_token: str) -> dict:
    return {"Authorization": f"Bearer {pr_token}"}


@pytest_asyncio.fixture
async def pr_procedure(db: AsyncSession) -> Procedure:
    proc = Procedure(
        id=uuid.uuid4(),
        name_ko="보톡스",
        slug="pr-botox",
        duration_minutes=30,
    )
    db.add(proc)
    await db.commit()
    await db.refresh(proc)
    return proc


@pytest_asyncio.fixture
async def pr_clinic_procedure(
    db: AsyncSession, pr_clinic: Clinic, pr_procedure: Procedure
) -> ClinicProcedure:
    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=pr_clinic.id,
        procedure_id=pr_procedure.id,
        difficulty_score=2,
        clinic_preference=1,
    )
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp


@pytest_asyncio.fixture
async def pricing_entry(
    db: AsyncSession, pr_clinic: Clinic, pr_clinic_procedure: ClinicProcedure
) -> ProcedurePricing:
    p = ProcedurePricing(
        id=uuid.uuid4(),
        clinic_procedure_id=pr_clinic_procedure.id,
        clinic_id=pr_clinic.id,
        regular_price=Decimal("150000"),
        event_price=Decimal("120000"),
        discount_rate=Decimal("20.00"),
        discount_warning=False,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


class TestCreatePricing:
    @pytest.mark.asyncio
    async def test_create_with_event_price(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pr_clinic_procedure: ClinicProcedure,
    ):
        resp = await client.post(
            "/api/v1/pricing",
            json={
                "clinic_procedure_id": str(pr_clinic_procedure.id),
                "regular_price": "100000",
                "event_price": "70000",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["regular_price"]) == 100000
        assert float(data["event_price"]) == 70000
        assert float(data["discount_rate"]) == 30.0
        assert data["discount_warning"] is False

    @pytest.mark.asyncio
    async def test_create_with_discount_warning(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pr_clinic_procedure: ClinicProcedure,
    ):
        resp = await client.post(
            "/api/v1/pricing",
            json={
                "clinic_procedure_id": str(pr_clinic_procedure.id),
                "regular_price": "200000",
                "event_price": "90000",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["discount_rate"]) == 55.0
        assert data["discount_warning"] is True

    @pytest.mark.asyncio
    async def test_create_without_event_price(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pr_clinic_procedure: ClinicProcedure,
    ):
        resp = await client.post(
            "/api/v1/pricing",
            json={
                "clinic_procedure_id": str(pr_clinic_procedure.id),
                "regular_price": "150000",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["discount_rate"] is None
        assert data["discount_warning"] is False


class TestListPricing:
    @pytest.mark.asyncio
    async def test_list_by_clinic(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pricing_entry: ProcedurePricing,
    ):
        resp = await client.get("/api/v1/pricing", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestUpdatePricing:
    @pytest.mark.asyncio
    async def test_update_event_price_recalculates_discount(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pricing_entry: ProcedurePricing,
    ):
        resp = await client.patch(
            f"/api/v1/pricing/{pricing_entry.id}",
            json={"event_price": "75000"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # 150000 → 75000 = 50% discount → warning
        assert float(data["discount_rate"]) == 50.0
        assert data["discount_warning"] is True

    @pytest.mark.asyncio
    async def test_update_regular_price_recalculates(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pricing_entry: ProcedurePricing,
    ):
        resp = await client.patch(
            f"/api/v1/pricing/{pricing_entry.id}",
            json={"regular_price": "200000"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # 200000 → 120000 = 40% discount
        assert float(data["discount_rate"]) == 40.0
        assert data["discount_warning"] is False


class TestDeletePricing:
    @pytest.mark.asyncio
    async def test_delete(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pricing_entry: ProcedurePricing,
    ):
        resp = await client.delete(
            f"/api/v1/pricing/{pricing_entry.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
