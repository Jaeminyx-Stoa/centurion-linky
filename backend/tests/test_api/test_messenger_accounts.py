import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Clinic, MessengerAccount, User


@pytest.fixture
async def account_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="계정테스트의원", slug="account-test")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def account_admin(db: AsyncSession, account_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=account_clinic.id,
        email="admin@account-test.com",
        password_hash=hash_password("password123"),
        name="관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def admin_token(account_admin: User) -> str:
    return create_access_token({"sub": str(account_admin.id)})


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


class TestCreateMessengerAccount:
    """POST /api/v1/messenger-accounts"""

    async def test_create_telegram_account(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/messenger-accounts",
            json={
                "messenger_type": "telegram",
                "account_name": "daybeaubot_jp",
                "display_name": "데이뷰의원 JP",
                "credentials": {"bot_token": "123456:ABC-DEF"},
                "target_countries": ["JP", "TW"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["messenger_type"] == "telegram"
        assert data["account_name"] == "daybeaubot_jp"
        assert data["is_active"] is True
        assert data["webhook_url"] is not None

    async def test_create_rejects_invalid_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/messenger-accounts",
            json={
                "messenger_type": "invalid_type",
                "account_name": "test",
                "credentials": {},
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/messenger-accounts",
            json={
                "messenger_type": "telegram",
                "account_name": "test",
                "credentials": {"bot_token": "test"},
            },
        )
        assert response.status_code == 401


class TestListMessengerAccounts:
    """GET /api/v1/messenger-accounts"""

    async def test_list_returns_clinic_accounts(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        account_clinic: Clinic,
    ):
        # Create two accounts
        for name in ["bot_jp", "bot_cn"]:
            acc = MessengerAccount(
                id=uuid.uuid4(),
                clinic_id=account_clinic.id,
                messenger_type="telegram",
                account_name=name,
                credentials={"bot_token": "test"},
            )
            db.add(acc)
        await db.commit()

        response = await client.get(
            "/api/v1/messenger-accounts", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_filters_by_messenger_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        account_clinic: Clinic,
    ):
        for mtype, name in [("telegram", "tg_bot"), ("line", "line_bot")]:
            acc = MessengerAccount(
                id=uuid.uuid4(),
                clinic_id=account_clinic.id,
                messenger_type=mtype,
                account_name=name,
                credentials={"token": "test"},
            )
            db.add(acc)
        await db.commit()

        response = await client.get(
            "/api/v1/messenger-accounts?messenger_type=telegram",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["messenger_type"] == "telegram"


class TestUpdateMessengerAccount:
    """PATCH /api/v1/messenger-accounts/{id}"""

    async def test_update_account(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        account_clinic: Clinic,
    ):
        acc = MessengerAccount(
            id=uuid.uuid4(),
            clinic_id=account_clinic.id,
            messenger_type="telegram",
            account_name="old_name",
            credentials={"bot_token": "test"},
        )
        db.add(acc)
        await db.commit()

        response = await client.patch(
            f"/api/v1/messenger-accounts/{acc.id}",
            json={"account_name": "new_name", "is_active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "new_name"
        assert data["is_active"] is False


class TestDeleteMessengerAccount:
    """DELETE /api/v1/messenger-accounts/{id}"""

    async def test_delete_account(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        account_clinic: Clinic,
    ):
        acc = MessengerAccount(
            id=uuid.uuid4(),
            clinic_id=account_clinic.id,
            messenger_type="telegram",
            account_name="to_delete",
            credentials={"bot_token": "test"},
        )
        db.add(acc)
        await db.commit()

        response = await client.delete(
            f"/api/v1/messenger-accounts/{acc.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.delete(
            f"/api/v1/messenger-accounts/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404
