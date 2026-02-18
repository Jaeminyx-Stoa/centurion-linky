import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.procedure_category import ProcedureCategory
from app.models.user import User


@pytest_asyncio.fixture
async def cat_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="카테고리의원", slug="cat-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def cat_admin(db: AsyncSession, cat_clinic: Clinic) -> User:
    from app.core.security import hash_password

    user = User(
        id=uuid.uuid4(),
        clinic_id=cat_clinic.id,
        email="cat-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="카테고리관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def cat_token(client: AsyncClient, cat_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "cat-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def auth_headers(cat_token: str) -> dict:
    return {"Authorization": f"Bearer {cat_token}"}


@pytest_asyncio.fixture
async def parent_category(db: AsyncSession) -> ProcedureCategory:
    cat = ProcedureCategory(
        id=uuid.uuid4(),
        name_ko="주사시술",
        slug="injection",
        sort_order=1,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@pytest_asyncio.fixture
async def child_category(
    db: AsyncSession, parent_category: ProcedureCategory
) -> ProcedureCategory:
    cat = ProcedureCategory(
        id=uuid.uuid4(),
        name_ko="보톡스",
        name_en="Botox",
        slug="botox",
        parent_id=parent_category.id,
        sort_order=1,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


class TestCreateCategory:
    @pytest.mark.asyncio
    async def test_create_root_category(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            "/api/v1/procedure-categories",
            json={"name_ko": "레이저시술", "slug": "laser"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name_ko"] == "레이저시술"
        assert data["slug"] == "laser"
        assert data["parent_id"] is None
        assert data["sort_order"] == 0

    @pytest.mark.asyncio
    async def test_create_child_category(
        self, client: AsyncClient, auth_headers: dict, parent_category: ProcedureCategory
    ):
        resp = await client.post(
            "/api/v1/procedure-categories",
            json={
                "name_ko": "필러",
                "name_en": "Filler",
                "slug": "filler",
                "parent_id": str(parent_category.id),
                "sort_order": 2,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["parent_id"] == str(parent_category.id)
        assert data["name_en"] == "Filler"

    @pytest.mark.asyncio
    async def test_create_duplicate_slug_fails(
        self, client: AsyncClient, auth_headers: dict, parent_category: ProcedureCategory
    ):
        resp = await client.post(
            "/api/v1/procedure-categories",
            json={"name_ko": "중복", "slug": "injection"},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestListCategories:
    @pytest.mark.asyncio
    async def test_list_returns_tree(
        self,
        client: AsyncClient,
        auth_headers: dict,
        parent_category: ProcedureCategory,
        child_category: ProcedureCategory,
    ):
        resp = await client.get(
            "/api/v1/procedure-categories",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should return root categories with children nested
        assert len(data) >= 1
        root = next(c for c in data if c["slug"] == "injection")
        assert len(root["children"]) == 1
        assert root["children"][0]["slug"] == "botox"

    @pytest.mark.asyncio
    async def test_list_flat(
        self,
        client: AsyncClient,
        auth_headers: dict,
        parent_category: ProcedureCategory,
        child_category: ProcedureCategory,
    ):
        resp = await client.get(
            "/api/v1/procedure-categories?flat=true",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2  # both parent and child


class TestGetCategory:
    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        parent_category: ProcedureCategory,
    ):
        resp = await client.get(
            f"/api/v1/procedure-categories/{parent_category.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name_ko"] == "주사시술"

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/procedure-categories/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestUpdateCategory:
    @pytest.mark.asyncio
    async def test_update_name(
        self,
        client: AsyncClient,
        auth_headers: dict,
        parent_category: ProcedureCategory,
    ):
        resp = await client.patch(
            f"/api/v1/procedure-categories/{parent_category.id}",
            json={"name_ko": "주사/필러시술", "name_en": "Injection"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name_ko"] == "주사/필러시술"
        assert data["name_en"] == "Injection"
