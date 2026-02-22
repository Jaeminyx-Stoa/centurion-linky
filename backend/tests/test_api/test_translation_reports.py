"""Tests for translation reports API endpoints."""

import uuid

import pytest
from httpx import AsyncClient


class TestTranslationReportsAPI:
    @pytest.mark.asyncio
    async def test_create_report_requires_auth(self, client: AsyncClient):
        """POST /translation-reports returns 401 without auth."""
        response = await client.post(
            "/api/v1/translation-reports/",
            json={
                "source_language": "ko",
                "target_language": "en",
                "original_text": "테스트",
                "translated_text": "test",
                "error_type": "wrong_term",
                "severity": "minor",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_reports_requires_auth(self, client: AsyncClient):
        """GET /translation-reports returns 401 without auth."""
        response = await client.get("/api/v1/translation-reports/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_stats_requires_auth(self, client: AsyncClient):
        """GET /translation-reports/stats returns 401 without auth."""
        response = await client.get("/api/v1/translation-reports/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_review_requires_auth(self, client: AsyncClient):
        """PATCH /translation-reports/{id}/review returns 401 without auth."""
        report_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/translation-reports/{report_id}/review",
            json={"status": "resolved"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_requires_auth(self, client: AsyncClient):
        """DELETE /translation-reports/{id} returns 401 without auth."""
        report_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/translation-reports/{report_id}"
        )
        assert response.status_code == 401
