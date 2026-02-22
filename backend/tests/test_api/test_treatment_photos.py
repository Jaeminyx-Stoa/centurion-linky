"""Tests for treatment photos API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
def mock_photo():
    photo = MagicMock()
    photo.id = uuid.uuid4()
    photo.clinic_id = uuid.uuid4()
    photo.customer_id = uuid.uuid4()
    photo.booking_id = None
    photo.procedure_id = None
    photo.photo_type = "before"
    photo.photo_url = "https://storage.test/photo.jpg"
    photo.thumbnail_url = None
    photo.description = "Before treatment"
    photo.taken_at = None
    photo.days_after_procedure = None
    photo.is_consent_given = True
    photo.is_portfolio_approved = False
    photo.approved_by = None
    photo.pair_id = None
    photo.created_at = "2025-01-01T00:00:00"
    photo.updated_at = "2025-01-01T00:00:00"
    return photo


class TestTreatmentPhotosAPI:
    @pytest.mark.asyncio
    async def test_list_photos_endpoint_exists(
        self, client: AsyncClient
    ):
        """GET /treatment-photos returns 401 without auth."""
        response = await client.get("/api/v1/treatment-photos/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_photo_endpoint_exists(
        self, client: AsyncClient
    ):
        """GET /treatment-photos/{id} returns 401 without auth."""
        photo_id = uuid.uuid4()
        response = await client.get(f"/api/v1/treatment-photos/{photo_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_photo_endpoint_exists(
        self, client: AsyncClient
    ):
        """DELETE /treatment-photos/{id} returns 401 without auth."""
        photo_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/treatment-photos/{photo_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_approve_endpoint_exists(
        self, client: AsyncClient
    ):
        """POST /treatment-photos/{id}/approve returns 401 without auth."""
        photo_id = uuid.uuid4()
        response = await client.post(f"/api/v1/treatment-photos/{photo_id}/approve")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_pairs_endpoint_exists(
        self, client: AsyncClient
    ):
        """GET /treatment-photos/pairs returns 401 without auth."""
        response = await client.get("/api/v1/treatment-photos/pairs")
        assert response.status_code == 401
