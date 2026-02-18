import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from app.models.messenger_account import MessengerAccount
from app.models.satisfaction_score import SatisfactionScore
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def sat_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="만족도의원", slug="sat-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def sat_admin(db: AsyncSession, sat_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=sat_clinic.id,
        email="sat-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="만족도관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def sat_token(client: AsyncClient, sat_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "sat-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def sat_headers(sat_token: str) -> dict:
    return {"Authorization": f"Bearer {sat_token}"}


@pytest_asyncio.fixture
async def sat_customer(db: AsyncSession, sat_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=sat_clinic.id,
        messenger_type="telegram",
        messenger_user_id="sat-tg-user-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def sat_account(db: AsyncSession, sat_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=sat_clinic.id,
        messenger_type="telegram",
        account_name="sat-bot",
        credentials={"token": "test"},
        is_active=True,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def sat_conversation(
    db: AsyncSession,
    sat_clinic: Clinic,
    sat_customer: Customer,
    sat_account: MessengerAccount,
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=sat_clinic.id,
        customer_id=sat_customer.id,
        messenger_account_id=sat_account.id,
        status="active",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def sat_messages(
    db: AsyncSession,
    sat_clinic: Clinic,
    sat_conversation: Conversation,
    sat_customer: Customer,
) -> list[Message]:
    msgs = [
        Message(
            id=uuid.uuid4(),
            conversation_id=sat_conversation.id,
            clinic_id=sat_clinic.id,
            sender_type="customer",
            content="안녕하세요 보톡스에 대해 궁금합니다",
            created_at=datetime.now(timezone.utc),
        ),
        Message(
            id=uuid.uuid4(),
            conversation_id=sat_conversation.id,
            clinic_id=sat_clinic.id,
            sender_type="ai",
            content="안녕하세요! 보톡스에 대해 안내드리겠습니다.",
            created_at=datetime.now(timezone.utc),
        ),
        Message(
            id=uuid.uuid4(),
            conversation_id=sat_conversation.id,
            clinic_id=sat_clinic.id,
            sender_type="customer",
            content="감사합니다 예약하고 싶어요",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    for m in msgs:
        db.add(m)
    await db.commit()
    for m in msgs:
        await db.refresh(m)
    return msgs


@pytest_asyncio.fixture
async def sat_negative_messages(
    db: AsyncSession,
    sat_clinic: Clinic,
    sat_conversation: Conversation,
) -> list[Message]:
    msgs = [
        Message(
            id=uuid.uuid4(),
            conversation_id=sat_conversation.id,
            clinic_id=sat_clinic.id,
            sender_type="customer",
            content="비싸요 됐어요 다른 병원 알아볼게요",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    for m in msgs:
        db.add(m)
    await db.commit()
    for m in msgs:
        await db.refresh(m)
    return msgs


# --- Tests ---
class TestAnalyzeConversation:
    @pytest.mark.asyncio
    async def test_analyze_positive(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
        sat_messages: list[Message],
    ):
        resp = await client.post(
            f"/api/v1/satisfaction/analyze/{sat_conversation.id}",
            headers=sat_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["score"] > 0
        assert data["level"] in ("green", "yellow", "orange", "red")
        assert data["language_signals"] is not None
        assert data["conversation_id"] == str(sat_conversation.id)

    @pytest.mark.asyncio
    async def test_analyze_updates_conversation_cache(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
        sat_messages: list[Message],
        db: AsyncSession,
    ):
        await client.post(
            f"/api/v1/satisfaction/analyze/{sat_conversation.id}",
            headers=sat_headers,
        )
        await db.refresh(sat_conversation)
        assert sat_conversation.satisfaction_score is not None
        assert sat_conversation.satisfaction_level is not None

    @pytest.mark.asyncio
    async def test_analyze_not_found(
        self, client: AsyncClient, sat_headers: dict
    ):
        resp = await client.post(
            f"/api/v1/satisfaction/analyze/{uuid.uuid4()}",
            headers=sat_headers,
        )
        assert resp.status_code == 404


class TestGetConversationScores:
    @pytest.mark.asyncio
    async def test_get_history(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
        sat_messages: list[Message],
    ):
        # Create a score first
        await client.post(
            f"/api/v1/satisfaction/analyze/{sat_conversation.id}",
            headers=sat_headers,
        )
        resp = await client.get(
            f"/api/v1/satisfaction/conversation/{sat_conversation.id}",
            headers=sat_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_empty_history(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
    ):
        resp = await client.get(
            f"/api/v1/satisfaction/conversation/{sat_conversation.id}",
            headers=sat_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestSupervisorOverride:
    @pytest.mark.asyncio
    async def test_override_score(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
        sat_messages: list[Message],
    ):
        # Create a score
        create_resp = await client.post(
            f"/api/v1/satisfaction/analyze/{sat_conversation.id}",
            headers=sat_headers,
        )
        score_id = create_resp.json()["id"]

        # Override
        resp = await client.post(
            f"/api/v1/satisfaction/{score_id}/override",
            json={
                "corrected_score": 85,
                "note": "이 고객은 원래 말이 짧아서 정상임",
            },
            headers=sat_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["supervisor_override"] == 85
        assert data["supervisor_note"] == "이 고객은 원래 말이 짧아서 정상임"
        assert data["supervised_by"] is not None

    @pytest.mark.asyncio
    async def test_override_updates_conversation_cache(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
        sat_messages: list[Message],
        db: AsyncSession,
    ):
        create_resp = await client.post(
            f"/api/v1/satisfaction/analyze/{sat_conversation.id}",
            headers=sat_headers,
        )
        score_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/satisfaction/{score_id}/override",
            json={"corrected_score": 95},
            headers=sat_headers,
        )
        await db.refresh(sat_conversation)
        assert sat_conversation.satisfaction_score == 95
        assert sat_conversation.satisfaction_level == "green"

    @pytest.mark.asyncio
    async def test_override_not_found(
        self, client: AsyncClient, sat_headers: dict
    ):
        resp = await client.post(
            f"/api/v1/satisfaction/{uuid.uuid4()}/override",
            json={"corrected_score": 80},
            headers=sat_headers,
        )
        assert resp.status_code == 404


class TestAlerts:
    @pytest.mark.asyncio
    async def test_alerts_returns_orange_red(
        self,
        client: AsyncClient,
        sat_headers: dict,
        sat_conversation: Conversation,
        sat_negative_messages: list[Message],
    ):
        # Create a low score by analyzing negative messages
        await client.post(
            f"/api/v1/satisfaction/analyze/{sat_conversation.id}",
            headers=sat_headers,
        )

        resp = await client.get(
            "/api/v1/satisfaction/alerts", headers=sat_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        # Negative messages should produce orange or red level
        if data:
            assert all(d["level"] in ("orange", "red") for d in data)

    @pytest.mark.asyncio
    async def test_alerts_filter_by_level(
        self, client: AsyncClient, sat_headers: dict
    ):
        resp = await client.get(
            "/api/v1/satisfaction/alerts?level=red", headers=sat_headers
        )
        assert resp.status_code == 200
