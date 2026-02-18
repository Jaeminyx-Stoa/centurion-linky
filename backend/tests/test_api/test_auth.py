import pytest
from httpx import AsyncClient

from app.models.user import User


class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_creates_clinic_and_admin(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "데이뷰의원",
                "clinic_slug": "daybeauclinic",
                "email": "admin@daybeauclinic.com",
                "password": "securepass123",
                "name": "김원장",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_rejects_duplicate_email(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "다른의원",
                "clinic_slug": "other-clinic",
                "email": test_user.email,
                "password": "securepass123",
                "name": "다른유저",
            },
        )
        assert response.status_code == 409

    async def test_register_rejects_duplicate_slug(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "다른의원",
                "clinic_slug": "test-clinic",  # 이미 존재
                "email": "new@example.com",
                "password": "securepass123",
                "name": "새유저",
            },
        )
        assert response.status_code == 409

    async def test_register_rejects_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "의원",
                "clinic_slug": "short-pw",
                "email": "short@example.com",
                "password": "short",
                "name": "유저",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_returns_tokens(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_rejects_wrong_password(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_login_rejects_nonexistent_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "whatever123",
            },
        )
        assert response.status_code == 401


class TestRefresh:
    """POST /api/v1/auth/refresh"""

    async def test_refresh_returns_new_tokens(self, client: AsyncClient, test_user: User):
        # 먼저 로그인
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # 리프레시
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_rejects_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    async def test_refresh_rejects_access_token(self, client: AsyncClient, test_user: User):
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        access_token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401


class TestMe:
    """GET /api/v1/auth/me"""

    async def test_me_returns_user_info(self, client: AsyncClient, test_user: User):
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        token = login_resp.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "테스트유저"
        assert data["role"] == "admin"

    async def test_me_rejects_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_rejects_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
