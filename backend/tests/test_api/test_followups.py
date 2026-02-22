import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.followup_rule import FollowupRule
from app.models.side_effect_keyword import SideEffectKeyword
from app.models.user import User


@pytest_asyncio.fixture
async def fu_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="팔로업의원", slug="fu-api-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def fu_admin(db: AsyncSession, fu_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=fu_clinic.id,
        email="fu-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="팔로업관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def fu_token(client: AsyncClient, fu_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "fu-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def fu_headers(fu_token: str) -> dict:
    return {"Authorization": f"Bearer {fu_token}"}


class TestFollowupRulesCRUD:
    @pytest.mark.asyncio
    async def test_create_rule(self, client: AsyncClient, fu_headers: dict):
        resp = await client.post(
            "/api/v1/followups/rules",
            json={
                "event_type": "recovery_check",
                "delay_days": 1,
                "delay_hours": 6,
                "message_template": {"ko": "상태 확인", "en": "Status check"},
            },
            headers=fu_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["event_type"] == "recovery_check"
        assert data["delay_days"] == 1
        assert data["delay_hours"] == 6

    @pytest.mark.asyncio
    async def test_list_rules(self, client: AsyncClient, fu_headers: dict):
        # Create a rule first
        await client.post(
            "/api/v1/followups/rules",
            json={"event_type": "result_check", "delay_days": 7},
            headers=fu_headers,
        )
        resp = await client.get("/api/v1/followups/rules", headers=fu_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_rule(self, client: AsyncClient, fu_headers: dict):
        create_resp = await client.post(
            "/api/v1/followups/rules",
            json={"event_type": "retouch_reminder", "delay_days": 30},
            headers=fu_headers,
        )
        rule_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/followups/rules/{rule_id}", headers=fu_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == rule_id

    @pytest.mark.asyncio
    async def test_update_rule(self, client: AsyncClient, fu_headers: dict):
        create_resp = await client.post(
            "/api/v1/followups/rules",
            json={"event_type": "recovery_check", "delay_days": 1},
            headers=fu_headers,
        )
        rule_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/followups/rules/{rule_id}",
            json={"delay_days": 2, "is_active": False},
            headers=fu_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["delay_days"] == 2
        assert resp.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_rule(self, client: AsyncClient, fu_headers: dict):
        create_resp = await client.post(
            "/api/v1/followups/rules",
            json={"event_type": "side_effect_check", "delay_days": 3},
            headers=fu_headers,
        )
        rule_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/followups/rules/{rule_id}", headers=fu_headers)
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client: AsyncClient, fu_headers: dict):
        resp = await client.get(
            f"/api/v1/followups/rules/{uuid.uuid4()}", headers=fu_headers
        )
        assert resp.status_code == 404


class TestSideEffectKeywords:
    @pytest.mark.asyncio
    async def test_create_keywords(self, client: AsyncClient, fu_headers: dict):
        resp = await client.post(
            "/api/v1/followups/keywords",
            json={
                "language": "ko",
                "keywords": ["아프다", "부어오르다", "빨갛다"],
                "severity": "normal",
            },
            headers=fu_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["language"] == "ko"
        assert len(data["keywords"]) == 3

    @pytest.mark.asyncio
    async def test_list_keywords(self, client: AsyncClient, fu_headers: dict):
        await client.post(
            "/api/v1/followups/keywords",
            json={"language": "en", "keywords": ["pain", "swelling"], "severity": "urgent"},
            headers=fu_headers,
        )
        resp = await client.get("/api/v1/followups/keywords", headers=fu_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestSideEffectAlerts:
    @pytest.mark.asyncio
    async def test_list_alerts_empty(self, client: AsyncClient, fu_headers: dict):
        resp = await client.get("/api/v1/followups/alerts", headers=fu_headers)
        assert resp.status_code == 200
        assert resp.json() == []
