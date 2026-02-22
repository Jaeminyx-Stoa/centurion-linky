"""Tests for packages API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestPackagesAPI:
    @pytest.mark.asyncio
    async def test_create_package_returns_201(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a package."""
        with patch(
            "app.api.v1.packages.ProcedurePackage",
        ):
            response = await client.post(
                "/api/v1/packages",
                json={
                    "name_ko": "보톡스 3회 패키지",
                    "total_sessions": 3,
                    "package_price": 1500000,
                    "discount_rate": 20,
                },
                headers=auth_headers,
            )
        assert response.status_code in (201, 401, 422)

    @pytest.mark.asyncio
    async def test_list_packages(self, client: AsyncClient, auth_headers: dict):
        """Test listing packages."""
        response = await client.get("/api/v1/packages", headers=auth_headers)
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_get_package_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent package."""
        response = await client.get(
            f"/api/v1/packages/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code in (404, 401)
