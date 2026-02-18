import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Clinic, Conversation, Customer, Message, MessengerAccount, User


# --- Fixtures ---

@pytest.fixture
async def conv_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="대화테스트의원", slug="conv-test")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def conv_admin(db: AsyncSession, conv_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=conv_clinic.id,
        email="admin@conv-test.com",
        password_hash=hash_password("password123"),
        name="대화관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def admin_token(conv_admin: User) -> str:
    return create_access_token({"sub": str(conv_admin.id)})


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def conv_account(db: AsyncSession, conv_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=conv_clinic.id,
        messenger_type="telegram",
        account_name="testbot",
        credentials={"bot_token": "test"},
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest.fixture
async def conv_customer(db: AsyncSession, conv_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=conv_clinic.id,
        messenger_type="telegram",
        messenger_user_id="user_123",
        name="유코",
        display_name="ゆうこ",
        country_code="JP",
        language_code="ja",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest.fixture
async def conv_conversation(
    db: AsyncSession,
    conv_clinic: Clinic,
    conv_customer: Customer,
    conv_account: MessengerAccount,
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=conv_clinic.id,
        customer_id=conv_customer.id,
        messenger_account_id=conv_account.id,
        status="active",
        ai_mode=True,
        last_message_preview="ボトックスはいくらですか？",
        unread_count=2,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@pytest.fixture
async def conv_messages(
    db: AsyncSession,
    conv_conversation: Conversation,
    conv_clinic: Clinic,
    conv_customer: Customer,
) -> list[Message]:
    msgs = [
        Message(
            id=uuid.uuid4(),
            conversation_id=conv_conversation.id,
            clinic_id=conv_clinic.id,
            sender_type="customer",
            sender_id=conv_customer.id,
            content="ボトックスはいくらですか？",
            content_type="text",
            original_language="ja",
            translated_content="보톡스 얼마예요?",
            translated_language="ko",
        ),
        Message(
            id=uuid.uuid4(),
            conversation_id=conv_conversation.id,
            clinic_id=conv_clinic.id,
            sender_type="ai",
            content="보톡스 가격을 안내드리겠습니다.",
            content_type="text",
        ),
    ]
    db.add_all(msgs)
    await db.commit()
    return msgs


# --- GET /api/v1/conversations ---

class TestListConversations:
    async def test_list_conversations(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        response = await client.get(
            "/api/v1/conversations", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["status"] == "active"

    async def test_list_filters_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        response = await client.get(
            "/api/v1/conversations?status=resolved",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    async def test_list_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/conversations")
        assert response.status_code == 401


# --- GET /api/v1/conversations/{id} ---

class TestGetConversation:
    async def test_get_conversation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        response = await client.get(
            f"/api/v1/conversations/{conv_conversation.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(conv_conversation.id)
        assert data["ai_mode"] is True

    async def test_get_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            f"/api/v1/conversations/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# --- GET /api/v1/conversations/{id}/messages ---

class TestGetMessages:
    async def test_get_messages(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
        conv_messages: list[Message],
    ):
        response = await client.get(
            f"/api/v1/conversations/{conv_conversation.id}/messages",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["sender_type"] == "customer"
        assert data[0]["translated_content"] == "보톡스 얼마예요?"

    async def test_get_messages_marks_as_read(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
        conv_messages: list[Message],
    ):
        response = await client.get(
            f"/api/v1/conversations/{conv_conversation.id}/messages",
            headers=auth_headers,
        )
        assert response.status_code == 200
        # Unread count should be reset
        conv_response = await client.get(
            f"/api/v1/conversations/{conv_conversation.id}",
            headers=auth_headers,
        )
        assert conv_response.json()["unread_count"] == 0


# --- POST /api/v1/conversations/{id}/messages ---

class TestSendMessage:
    async def test_send_message_from_staff(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        response = await client.post(
            f"/api/v1/conversations/{conv_conversation.id}/messages",
            json={"content": "안녕하세요, 도와드리겠습니다."},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["sender_type"] == "staff"
        assert data["content"] == "안녕하세요, 도와드리겠습니다."


# --- POST /api/v1/conversations/{id}/toggle-ai ---

class TestToggleAI:
    async def test_toggle_ai_off(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        response = await client.post(
            f"/api/v1/conversations/{conv_conversation.id}/toggle-ai",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_mode"] is False

    async def test_toggle_ai_on(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        # First toggle off
        await client.post(
            f"/api/v1/conversations/{conv_conversation.id}/toggle-ai",
            headers=auth_headers,
        )
        # Then toggle on
        response = await client.post(
            f"/api/v1/conversations/{conv_conversation.id}/toggle-ai",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ai_mode"] is True


# --- POST /api/v1/conversations/{id}/resolve ---

class TestResolveConversation:
    async def test_resolve(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_conversation: Conversation,
    ):
        response = await client.post(
            f"/api/v1/conversations/{conv_conversation.id}/resolve",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"


# --- GET /api/v1/customers/{id} ---

class TestGetCustomer:
    async def test_get_customer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_customer: Customer,
    ):
        response = await client.get(
            f"/api/v1/customers/{conv_customer.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "유코"
        assert data["country_code"] == "JP"
        assert data["language_code"] == "ja"

    async def test_get_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            f"/api/v1/customers/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# --- PATCH /api/v1/customers/{id} ---

class TestUpdateCustomer:
    async def test_update_customer_tags(
        self,
        client: AsyncClient,
        auth_headers: dict,
        conv_customer: Customer,
    ):
        response = await client.patch(
            f"/api/v1/customers/{conv_customer.id}",
            json={"tags": ["VIP", "일본"], "notes": "보톡스 관심"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "VIP" in data["tags"]
        assert data["notes"] == "보톡스 관심"
