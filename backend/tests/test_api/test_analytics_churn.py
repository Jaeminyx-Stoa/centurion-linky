"""Tests for churn risk analytics API endpoints."""

import pytest
from httpx import AsyncClient


class TestAnalyticsChurnAPI:
    @pytest.mark.asyncio
    async def test_churn_risk_requires_auth(self, client: AsyncClient):
        """GET /analytics/churn-risk returns 401 without auth."""
        response = await client.get("/api/v1/analytics/churn-risk")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revisit_summary_requires_auth(self, client: AsyncClient):
        """GET /analytics/revisit-summary returns 401 without auth."""
        response = await client.get("/api/v1/analytics/revisit-summary")
        assert response.status_code == 401
