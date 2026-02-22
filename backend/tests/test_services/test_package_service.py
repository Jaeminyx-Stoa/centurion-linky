"""Tests for PackageService."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.services.package_service import PackageService


@pytest.fixture
def clinic_id():
    return uuid.uuid4()


def _make_package(clinic_id, items=None, total_sessions=3):
    pkg = MagicMock()
    pkg.id = uuid.uuid4()
    pkg.clinic_id = clinic_id
    pkg.is_active = True
    pkg.total_sessions = total_sessions
    pkg.items = items or []
    return pkg


class TestPackageService:
    @pytest.mark.asyncio
    async def test_create_enrollment_generates_sessions(self, clinic_id):
        cp_id = str(uuid.uuid4())
        pkg = _make_package(
            clinic_id,
            items=[
                {"clinic_procedure_id": cp_id, "sessions": 3, "interval_days": 14}
            ],
        )

        db = AsyncMock()
        db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=pkg)
        )
        added_objects = []
        db.add = lambda obj: added_objects.append(obj)

        svc = PackageService(db)
        enrollment = await svc.create_enrollment(pkg.id, uuid.uuid4(), clinic_id)

        assert enrollment.status == "active"
        assert enrollment.sessions_completed == 0
        # 1 enrollment + 3 sessions = 4 objects added
        assert len(added_objects) == 4

    @pytest.mark.asyncio
    async def test_create_enrollment_package_not_found(self, clinic_id):
        db = AsyncMock()
        db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        svc = PackageService(db)
        with pytest.raises(NotFoundError):
            await svc.create_enrollment(uuid.uuid4(), uuid.uuid4(), clinic_id)

    @pytest.mark.asyncio
    async def test_complete_session_increments_count(self, clinic_id):
        enrollment = MagicMock()
        enrollment.id = uuid.uuid4()
        enrollment.clinic_id = clinic_id
        enrollment.sessions_completed = 0

        session1 = MagicMock()
        session1.session_number = 1
        session1.status = "pending"
        session1.scheduled_date = date.today()

        session2 = MagicMock()
        session2.session_number = 2
        session2.status = "pending"
        session2.scheduled_date = date.today()

        enrollment.sessions = [session1, session2]

        db = AsyncMock()
        db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=enrollment)
        )

        svc = PackageService(db)
        result = await svc.complete_session(enrollment.id, 1, clinic_id)

        assert result.status == "completed"
        assert enrollment.sessions_completed == 1
        assert enrollment.status != "completed"  # Still has pending sessions

    @pytest.mark.asyncio
    async def test_complete_last_session_completes_enrollment(self, clinic_id):
        enrollment = MagicMock()
        enrollment.id = uuid.uuid4()
        enrollment.clinic_id = clinic_id
        enrollment.sessions_completed = 0

        session1 = MagicMock()
        session1.session_number = 1
        session1.status = "pending"
        session1.scheduled_date = date.today()

        enrollment.sessions = [session1]

        db = AsyncMock()
        db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=enrollment)
        )

        svc = PackageService(db)
        await svc.complete_session(enrollment.id, 1, clinic_id)

        assert enrollment.sessions_completed == 1
        assert enrollment.status == "completed"
        assert enrollment.next_session_date is None

    @pytest.mark.asyncio
    async def test_complete_session_enrollment_not_found(self, clinic_id):
        db = AsyncMock()
        db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        svc = PackageService(db)
        with pytest.raises(NotFoundError):
            await svc.complete_session(uuid.uuid4(), 1, clinic_id)
