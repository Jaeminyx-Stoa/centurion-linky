"""Tests for TranslationReportService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.translation_report_service import TranslationReportService


@pytest.fixture
def clinic_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


class TestTranslationReportService:
    @pytest.mark.asyncio
    async def test_create_report(self, clinic_id, user_id):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        svc = TranslationReportService(db)
        report = await svc.create_report(
            clinic_id=clinic_id,
            reported_by=user_id,
            source_language="ko",
            target_language="en",
            original_text="보톡스 시술",
            translated_text="Botox treatment",
            error_type="wrong_term",
            severity="critical",
        )

        assert report.clinic_id == clinic_id
        assert report.reported_by == user_id
        assert report.source_language == "ko"
        assert report.target_language == "en"
        assert report.error_type == "wrong_term"
        assert report.severity == "critical"
        assert report.status == "pending"
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_report_updates_status(self, clinic_id, user_id):
        report = MagicMock()
        report.status = "pending"

        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=report))
        )
        db.flush = AsyncMock()

        reviewer_id = uuid.uuid4()
        svc = TranslationReportService(db)
        result = await svc.review_report(
            report_id=uuid.uuid4(),
            clinic_id=clinic_id,
            reviewer_id=reviewer_id,
            status="resolved",
            reviewer_notes="Corrected to proper medical term",
            corrected_text="Botulinum toxin procedure",
        )

        assert result.status == "resolved"
        assert result.reviewer_id == reviewer_id
        assert result.corrected_text == "Botulinum toxin procedure"
        assert result.reviewed_at is not None

    @pytest.mark.asyncio
    async def test_review_not_found_raises(self, clinic_id):
        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        svc = TranslationReportService(db)
        with pytest.raises(Exception, match="not found"):
            await svc.review_report(
                report_id=uuid.uuid4(),
                clinic_id=clinic_id,
                reviewer_id=uuid.uuid4(),
                status="resolved",
            )

    @pytest.mark.asyncio
    async def test_delete_report_not_found_raises(self, clinic_id):
        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        svc = TranslationReportService(db)
        with pytest.raises(Exception, match="not found"):
            await svc.delete_report(uuid.uuid4(), clinic_id)

    @pytest.mark.asyncio
    async def test_delete_report_success(self, clinic_id):
        report = MagicMock()
        db = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=report))
        )
        db.delete = AsyncMock()
        db.flush = AsyncMock()

        svc = TranslationReportService(db)
        await svc.delete_report(uuid.uuid4(), clinic_id)

        db.delete.assert_awaited_once_with(report)
