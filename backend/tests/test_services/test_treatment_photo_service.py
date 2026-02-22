"""Tests for TreatmentPhotoService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.treatment_photo_service import TreatmentPhotoService


@pytest.fixture
def clinic_id():
    return uuid.uuid4()


@pytest.fixture
def customer_id():
    return uuid.uuid4()


class TestTreatmentPhotoService:
    @pytest.mark.asyncio
    async def test_create_photo(self, clinic_id, customer_id):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        svc = TreatmentPhotoService(db)
        photo = await svc.create_photo(
            clinic_id=clinic_id,
            photo_url="https://storage.test/photo.jpg",
            thumbnail_url="https://storage.test/thumb.jpg",
            customer_id=customer_id,
            photo_type="before",
            description="시술 전 사진",
            is_consent_given=True,
        )

        assert photo.clinic_id == clinic_id
        assert photo.customer_id == customer_id
        assert photo.photo_type == "before"
        assert photo.photo_url == "https://storage.test/photo.jpg"
        assert photo.is_consent_given is True
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_photo_not_found_raises(self, clinic_id):
        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        svc = TreatmentPhotoService(db)
        with pytest.raises(Exception, match="not found"):
            await svc.get_photo(uuid.uuid4(), clinic_id)

    @pytest.mark.asyncio
    async def test_approve_for_portfolio(self, clinic_id):
        photo = MagicMock()
        photo.is_portfolio_approved = False
        photo.approved_by = None

        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=photo))
        )
        db.flush = AsyncMock()

        approver_id = uuid.uuid4()
        svc = TreatmentPhotoService(db)
        result = await svc.approve_for_portfolio(uuid.uuid4(), clinic_id, approver_id)

        assert result.is_portfolio_approved is True
        assert result.approved_by == approver_id

    @pytest.mark.asyncio
    async def test_delete_photo(self, clinic_id):
        photo = MagicMock()
        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=photo))
        )
        db.delete = AsyncMock()
        db.flush = AsyncMock()

        svc = TreatmentPhotoService(db)
        await svc.delete_photo(uuid.uuid4(), clinic_id)

        db.delete.assert_awaited_once_with(photo)

    @pytest.mark.asyncio
    async def test_update_photo_sets_fields(self, clinic_id):
        photo = MagicMock()
        photo.description = "old"

        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=photo))
        )
        db.flush = AsyncMock()

        svc = TreatmentPhotoService(db)
        result = await svc.update_photo(
            uuid.uuid4(), clinic_id, description="새 설명"
        )

        assert result.description == "새 설명"
