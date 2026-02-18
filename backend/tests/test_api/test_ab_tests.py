import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.messenger_account import MessengerAccount
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def ab_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="AB테스트의원", slug="ab-api-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def ab_admin(db: AsyncSession, ab_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        email="ab-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="AB관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def ab_token(client: AsyncClient, ab_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ab-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def ab_headers(ab_token: str) -> dict:
    return {"Authorization": f"Bearer {ab_token}"}


@pytest_asyncio.fixture
async def ab_conversation(db: AsyncSession, ab_clinic: Clinic) -> Conversation:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        messenger_type="telegram",
        messenger_user_id="ab-api-tg-1",
    )
    db.add(customer)
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        messenger_type="telegram",
        account_name="ab-api-bot",
        credentials={"token": "test"},
        is_active=True,
    )
    db.add(account)
    await db.flush()
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=ab_clinic.id,
        customer_id=customer.id,
        messenger_account_id=account.id,
        status="active",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


# --- Tests ---
class TestCreateABTest:
    @pytest.mark.asyncio
    async def test_create(self, client: AsyncClient, ab_headers: dict):
        resp = await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "인사말 A/B 테스트",
                "test_type": "greeting",
                "variants": [
                    {"name": "A안", "config": {"greeting": "안녕하세요!"}},
                    {"name": "B안", "config": {"greeting": "반갑습니다!"}},
                ],
            },
            headers=ab_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "인사말 A/B 테스트"
        assert data["status"] == "draft"
        assert len(data["variants"]) == 2

    @pytest.mark.asyncio
    async def test_requires_min_2_variants(
        self, client: AsyncClient, ab_headers: dict
    ):
        resp = await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "부족한 테스트",
                "test_type": "prompt",
                "variants": [{"name": "A안"}],
            },
            headers=ab_headers,
        )
        assert resp.status_code == 422


class TestListABTests:
    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient, ab_headers: dict):
        resp = await client.get("/api/v1/ab-tests", headers=ab_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_with_items(
        self, client: AsyncClient, ab_headers: dict
    ):
        await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "테스트1",
                "test_type": "greeting",
                "variants": [{"name": "A"}, {"name": "B"}],
            },
            headers=ab_headers,
        )
        resp = await client.get("/api/v1/ab-tests", headers=ab_headers)
        assert len(resp.json()) == 1


class TestUpdateABTest:
    @pytest.mark.asyncio
    async def test_activate(self, client: AsyncClient, ab_headers: dict):
        create_resp = await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "활성화 대상",
                "test_type": "prompt",
                "variants": [{"name": "A"}, {"name": "B"}],
            },
            headers=ab_headers,
        )
        test_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/ab-tests/{test_id}",
            json={"is_active": True},
            headers=ab_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True
        assert resp.json()["status"] == "active"
        assert resp.json()["started_at"] is not None

    @pytest.mark.asyncio
    async def test_deactivate(self, client: AsyncClient, ab_headers: dict):
        create_resp = await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "비활성화 대상",
                "test_type": "prompt",
                "variants": [{"name": "A"}, {"name": "B"}],
            },
            headers=ab_headers,
        )
        test_id = create_resp.json()["id"]

        # Activate first
        await client.patch(
            f"/api/v1/ab-tests/{test_id}",
            json={"is_active": True},
            headers=ab_headers,
        )
        # Then deactivate
        resp = await client.patch(
            f"/api/v1/ab-tests/{test_id}",
            json={"is_active": False},
            headers=ab_headers,
        )
        assert resp.json()["status"] == "completed"
        assert resp.json()["ended_at"] is not None


class TestRecordResult:
    @pytest.mark.asyncio
    async def test_record(
        self,
        client: AsyncClient,
        ab_headers: dict,
        ab_conversation: Conversation,
    ):
        # Create and activate test
        create_resp = await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "결과 기록 테스트",
                "test_type": "prompt",
                "variants": [{"name": "A"}, {"name": "B"}],
            },
            headers=ab_headers,
        )
        test_id = create_resp.json()["id"]
        variant_id = create_resp.json()["variants"][0]["id"]

        resp = await client.post(
            f"/api/v1/ab-tests/{test_id}/results",
            json={
                "variant_id": variant_id,
                "conversation_id": str(ab_conversation.id),
                "outcome": "booked",
            },
            headers=ab_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["outcome"] == "booked"


class TestGetStats:
    @pytest.mark.asyncio
    async def test_stats(self, client: AsyncClient, ab_headers: dict):
        create_resp = await client.post(
            "/api/v1/ab-tests",
            json={
                "name": "통계 테스트",
                "test_type": "prompt",
                "variants": [{"name": "A"}, {"name": "B"}],
            },
            headers=ab_headers,
        )
        test_id = create_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/ab-tests/{test_id}/stats", headers=ab_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2
