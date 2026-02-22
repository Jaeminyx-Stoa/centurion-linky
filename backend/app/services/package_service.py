"""Package enrollment and session management service."""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.package_enrollment import PackageEnrollment
from app.models.package_session import PackageSession
from app.models.procedure_package import ProcedurePackage


class PackageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_enrollment(
        self,
        package_id: uuid.UUID,
        customer_id: uuid.UUID,
        clinic_id: uuid.UUID,
    ) -> PackageEnrollment:
        """Create an enrollment and auto-generate all sessions."""
        # Load package
        result = await self.db.execute(
            select(ProcedurePackage).where(
                ProcedurePackage.id == package_id,
                ProcedurePackage.clinic_id == clinic_id,
                ProcedurePackage.is_active.is_(True),
            )
        )
        package = result.scalar_one_or_none()
        if package is None:
            raise NotFoundError("Package not found")

        now = datetime.now(timezone.utc)
        enrollment = PackageEnrollment(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            customer_id=customer_id,
            package_id=package_id,
            status="active",
            purchased_at=now,
            sessions_completed=0,
        )
        self.db.add(enrollment)

        # Generate sessions from package items
        items = package.items or []
        if isinstance(items, dict):
            items = items.get("items", [])

        session_number = 0
        base_date = date.today()
        for item in items:
            interval_days = item.get("interval_days", 14)
            sessions_count = item.get("sessions", 1)
            cp_id = item.get("clinic_procedure_id")

            for s in range(sessions_count):
                session_number += 1
                scheduled = base_date + timedelta(days=interval_days * s) if interval_days > 0 else None
                session = PackageSession(
                    id=uuid.uuid4(),
                    enrollment_id=enrollment.id,
                    session_number=session_number,
                    clinic_procedure_id=uuid.UUID(cp_id) if cp_id else None,
                    status="pending",
                    scheduled_date=scheduled,
                )
                self.db.add(session)

            base_date += timedelta(days=interval_days * sessions_count)

        # Set next session date
        if session_number > 0:
            enrollment.next_session_date = date.today()

        await self.db.flush()
        return enrollment

    async def complete_session(
        self,
        enrollment_id: uuid.UUID,
        session_number: int,
        clinic_id: uuid.UUID,
    ) -> PackageSession:
        """Complete a session and update enrollment progress."""
        # Load enrollment
        result = await self.db.execute(
            select(PackageEnrollment)
            .options(selectinload(PackageEnrollment.sessions))
            .where(
                PackageEnrollment.id == enrollment_id,
                PackageEnrollment.clinic_id == clinic_id,
            )
        )
        enrollment = result.scalar_one_or_none()
        if enrollment is None:
            raise NotFoundError("Enrollment not found")

        # Find the session
        session = next(
            (s for s in enrollment.sessions if s.session_number == session_number),
            None,
        )
        if session is None:
            raise NotFoundError("Session not found")

        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)

        enrollment.sessions_completed += 1

        # Check if all sessions are done
        total = len(enrollment.sessions)
        if enrollment.sessions_completed >= total:
            enrollment.status = "completed"
            enrollment.next_session_date = None
        else:
            # Find next pending session
            next_session = next(
                (s for s in sorted(enrollment.sessions, key=lambda x: x.session_number)
                 if s.status == "pending"),
                None,
            )
            if next_session and next_session.scheduled_date:
                enrollment.next_session_date = next_session.scheduled_date

        await self.db.flush()
        return session
