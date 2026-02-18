import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def persona_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="페르소나의원", slug="persona-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def persona_admin(db: AsyncSession, persona_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=persona_clinic.id,
        email="persona-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="페르소나관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def persona_token(client: AsyncClient, persona_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "persona-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def persona_headers(persona_token: str) -> dict:
    return {"Authorization": f"Bearer {persona_token}"}


# --- Tests ---
class TestCreatePersona:
    @pytest.mark.asyncio
    async def test_create_minimal(
        self, client: AsyncClient, persona_headers: dict
    ):
        resp = await client.post(
            "/api/v1/ai-personas",
            json={"name": "상담사A"},
            headers=persona_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "상담사A"
        assert data["is_active"] is True
        assert data["is_default"] is False

    @pytest.mark.asyncio
    async def test_create_full(
        self, client: AsyncClient, persona_headers: dict
    ):
        resp = await client.post(
            "/api/v1/ai-personas",
            json={
                "name": "VIP상담사",
                "personality": "친절하고 전문적인 상담사",
                "system_prompt": "당신은 VIP 고객 전담 상담사입니다.",
                "avatar_url": "https://example.com/avatar.png",
                "is_default": True,
            },
            headers=persona_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["personality"] == "친절하고 전문적인 상담사"
        assert data["system_prompt"] == "당신은 VIP 고객 전담 상담사입니다."
        assert data["is_default"] is True


class TestListPersonas:
    @pytest.mark.asyncio
    async def test_list_empty(
        self, client: AsyncClient, persona_headers: dict
    ):
        resp = await client.get(
            "/api/v1/ai-personas", headers=persona_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_with_items(
        self, client: AsyncClient, persona_headers: dict
    ):
        await client.post(
            "/api/v1/ai-personas",
            json={"name": "상담사A"},
            headers=persona_headers,
        )
        await client.post(
            "/api/v1/ai-personas",
            json={"name": "상담사B"},
            headers=persona_headers,
        )
        resp = await client.get(
            "/api/v1/ai-personas", headers=persona_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestGetPersona:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, persona_headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/ai-personas",
            json={"name": "조회대상"},
            headers=persona_headers,
        )
        persona_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/ai-personas/{persona_id}",
            headers=persona_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "조회대상"

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, persona_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/ai-personas/{uuid.uuid4()}",
            headers=persona_headers,
        )
        assert resp.status_code == 404


class TestUpdatePersona:
    @pytest.mark.asyncio
    async def test_update_name(
        self, client: AsyncClient, persona_headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/ai-personas",
            json={"name": "원래이름"},
            headers=persona_headers,
        )
        persona_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/ai-personas/{persona_id}",
            json={"name": "새이름"},
            headers=persona_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "새이름"

    @pytest.mark.asyncio
    async def test_update_partial(
        self, client: AsyncClient, persona_headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/ai-personas",
            json={"name": "부분수정", "personality": "원래성격"},
            headers=persona_headers,
        )
        persona_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/ai-personas/{persona_id}",
            json={"personality": "새로운 성격"},
            headers=persona_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["personality"] == "새로운 성격"
        assert resp.json()["name"] == "부분수정"

    @pytest.mark.asyncio
    async def test_deactivate(
        self, client: AsyncClient, persona_headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/ai-personas",
            json={"name": "비활성화대상"},
            headers=persona_headers,
        )
        persona_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/ai-personas/{persona_id}",
            json={"is_active": False},
            headers=persona_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


class TestDeletePersona:
    @pytest.mark.asyncio
    async def test_delete_existing(
        self, client: AsyncClient, persona_headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/ai-personas",
            json={"name": "삭제대상"},
            headers=persona_headers,
        )
        persona_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/ai-personas/{persona_id}",
            headers=persona_headers,
        )
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = await client.get(
            f"/api/v1/ai-personas/{persona_id}",
            headers=persona_headers,
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self, client: AsyncClient, persona_headers: dict
    ):
        resp = await client.delete(
            f"/api/v1/ai-personas/{uuid.uuid4()}",
            headers=persona_headers,
        )
        assert resp.status_code == 404
