import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.procedure import Procedure
from app.models.procedure_category import ProcedureCategory
from app.models.user import User


@pytest_asyncio.fixture
async def proc_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="시술의원", slug="proc-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def proc_admin(db: AsyncSession, proc_clinic: Clinic) -> User:
    from app.core.security import hash_password

    user = User(
        id=uuid.uuid4(),
        clinic_id=proc_clinic.id,
        email="proc-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="시술관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def proc_token(client: AsyncClient, proc_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "proc-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def auth_headers(proc_token: str) -> dict:
    return {"Authorization": f"Bearer {proc_token}"}


@pytest_asyncio.fixture
async def proc_category(db: AsyncSession) -> ProcedureCategory:
    cat = ProcedureCategory(
        id=uuid.uuid4(),
        name_ko="주사시술",
        slug="injection-proc",
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@pytest_asyncio.fixture
async def base_procedure(
    db: AsyncSession, proc_category: ProcedureCategory
) -> Procedure:
    proc = Procedure(
        id=uuid.uuid4(),
        category_id=proc_category.id,
        name_ko="보톡스",
        name_en="Botox",
        slug="botox-proc",
        description_ko="보툴리눔 톡신을 이용한 주름 개선 시술",
        duration_minutes=30,
        effect_duration="3~6개월",
        downtime_days=0,
        pain_level=3,
    )
    db.add(proc)
    await db.commit()
    await db.refresh(proc)
    return proc


class TestCreateProcedure:
    @pytest.mark.asyncio
    async def test_create_procedure(
        self, client: AsyncClient, auth_headers: dict, proc_category: ProcedureCategory
    ):
        resp = await client.post(
            "/api/v1/procedures",
            json={
                "name_ko": "필러",
                "name_en": "Filler",
                "slug": "filler",
                "category_id": str(proc_category.id),
                "duration_minutes": 45,
                "pain_level": 4,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name_ko"] == "필러"
        assert data["name_en"] == "Filler"
        assert data["duration_minutes"] == 45
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_without_category(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            "/api/v1/procedures",
            json={"name_ko": "리프팅", "slug": "lifting"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["category_id"] is None

    @pytest.mark.asyncio
    async def test_create_duplicate_slug_fails(
        self, client: AsyncClient, auth_headers: dict, base_procedure: Procedure
    ):
        resp = await client.post(
            "/api/v1/procedures",
            json={"name_ko": "중복", "slug": "botox-proc"},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestListProcedures:
    @pytest.mark.asyncio
    async def test_list_all(
        self, client: AsyncClient, auth_headers: dict, base_procedure: Procedure
    ):
        resp = await client.get("/api/v1/procedures", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_by_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        base_procedure: Procedure,
        proc_category: ProcedureCategory,
    ):
        resp = await client.get(
            f"/api/v1/procedures?category_id={proc_category.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(p["category_id"] == str(proc_category.id) for p in data)

    @pytest.mark.asyncio
    async def test_list_search_by_name(
        self, client: AsyncClient, auth_headers: dict, base_procedure: Procedure
    ):
        resp = await client.get(
            "/api/v1/procedures?q=보톡스",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name_ko"] == "보톡스"


class TestGetProcedure:
    @pytest.mark.asyncio
    async def test_get_by_id(
        self, client: AsyncClient, auth_headers: dict, base_procedure: Procedure
    ):
        resp = await client.get(
            f"/api/v1/procedures/{base_procedure.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name_ko"] == "보톡스"
        assert data["duration_minutes"] == 30

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/procedures/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestUpdateProcedure:
    @pytest.mark.asyncio
    async def test_update_fields(
        self, client: AsyncClient, auth_headers: dict, base_procedure: Procedure
    ):
        resp = await client.patch(
            f"/api/v1/procedures/{base_procedure.id}",
            json={
                "description_ko": "업데이트된 설명",
                "duration_minutes": 20,
                "pain_level": 2,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description_ko"] == "업데이트된 설명"
        assert data["duration_minutes"] == 20
        assert data["pain_level"] == 2
        # Unchanged fields preserved
        assert data["name_ko"] == "보톡스"

    @pytest.mark.asyncio
    async def test_deactivate(
        self, client: AsyncClient, auth_headers: dict, base_procedure: Procedure
    ):
        resp = await client.patch(
            f"/api/v1/procedures/{base_procedure.id}",
            json={"is_active": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False
