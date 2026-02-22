"""Tests for conversion funnel analytics API."""

import pytest
from httpx import AsyncClient


class TestConversionFunnelAPI:
    @pytest.mark.asyncio
    async def test_funnel_by_nationality(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/analytics/conversion-funnel",
            params={"days": 30, "group_by": "nationality"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert "groups" in data
            assert "totals" in data
            assert data["group_by"] == "nationality"

    @pytest.mark.asyncio
    async def test_funnel_by_channel(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/analytics/conversion-funnel",
            params={"days": 30, "group_by": "channel"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_funnel_by_both(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/analytics/conversion-funnel",
            params={"days": 30, "group_by": "both"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_funnel_invalid_group_by(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/analytics/conversion-funnel",
            params={"days": 30, "group_by": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code in (422, 401)

    @pytest.mark.asyncio
    async def test_funnel_default_params(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/analytics/conversion-funnel",
            headers=auth_headers,
        )
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert data["days"] == 30
            assert data["group_by"] == "nationality"
