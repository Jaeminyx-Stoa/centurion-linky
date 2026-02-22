"""Translation QA reporting and review service."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.message import Message
from app.models.translation_report import TranslationReport


class TranslationReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        clinic_id: uuid.UUID,
        reported_by: uuid.UUID,
        *,
        source_language: str,
        target_language: str,
        original_text: str,
        translated_text: str,
        error_type: str,
        severity: str,
        message_id: uuid.UUID | None = None,
        corrected_text: str | None = None,
        medical_term_id: uuid.UUID | None = None,
    ) -> TranslationReport:
        report = TranslationReport(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            reported_by=reported_by,
            message_id=message_id,
            source_language=source_language,
            target_language=target_language,
            original_text=original_text,
            translated_text=translated_text,
            corrected_text=corrected_text,
            error_type=error_type,
            severity=severity,
            medical_term_id=medical_term_id,
            status="pending",
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def list_reports(
        self,
        clinic_id: uuid.UUID,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TranslationReport], int]:
        query = select(TranslationReport).where(
            TranslationReport.clinic_id == clinic_id
        )
        count_query = select(func.count(TranslationReport.id)).where(
            TranslationReport.clinic_id == clinic_id
        )

        if status:
            query = query.where(TranslationReport.status == status)
            count_query = count_query.where(TranslationReport.status == status)
        if severity:
            query = query.where(TranslationReport.severity == severity)
            count_query = count_query.where(TranslationReport.severity == severity)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            query.order_by(TranslationReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        reports = list(result.scalars().all())
        return reports, total

    async def review_report(
        self,
        report_id: uuid.UUID,
        clinic_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        status: str,
        reviewer_notes: str | None = None,
        corrected_text: str | None = None,
    ) -> TranslationReport:
        result = await self.db.execute(
            select(TranslationReport).where(
                TranslationReport.id == report_id,
                TranslationReport.clinic_id == clinic_id,
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise NotFoundError("Translation report not found")

        report.status = status
        report.reviewer_id = reviewer_id
        report.reviewer_notes = reviewer_notes
        report.reviewed_at = datetime.now(timezone.utc)
        if corrected_text:
            report.corrected_text = corrected_text
        await self.db.flush()
        return report

    async def get_qa_stats(self, clinic_id: uuid.UUID, days: int = 30) -> dict:
        """Get translation QA statistics."""
        from datetime import date, timedelta

        cutoff = date.today() - timedelta(days=days)

        # Total reports
        total_result = await self.db.execute(
            select(func.count(TranslationReport.id)).where(
                TranslationReport.clinic_id == clinic_id,
                func.date(TranslationReport.created_at) >= cutoff,
            )
        )
        total_reports = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(
                TranslationReport.status,
                func.count(TranslationReport.id),
            )
            .where(
                TranslationReport.clinic_id == clinic_id,
                func.date(TranslationReport.created_at) >= cutoff,
            )
            .group_by(TranslationReport.status)
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # Critical count
        critical_result = await self.db.execute(
            select(func.count(TranslationReport.id)).where(
                TranslationReport.clinic_id == clinic_id,
                TranslationReport.severity == "critical",
                func.date(TranslationReport.created_at) >= cutoff,
            )
        )
        critical_count = critical_result.scalar() or 0

        # By error type
        error_result = await self.db.execute(
            select(
                TranslationReport.error_type,
                func.count(TranslationReport.id),
            )
            .where(
                TranslationReport.clinic_id == clinic_id,
                func.date(TranslationReport.created_at) >= cutoff,
            )
            .group_by(TranslationReport.error_type)
        )
        by_error_type = {row[0]: row[1] for row in error_result.all()}

        # By language pair
        lang_result = await self.db.execute(
            select(
                TranslationReport.source_language,
                TranslationReport.target_language,
                func.count(TranslationReport.id),
            )
            .where(
                TranslationReport.clinic_id == clinic_id,
                func.date(TranslationReport.created_at) >= cutoff,
            )
            .group_by(
                TranslationReport.source_language,
                TranslationReport.target_language,
            )
        )
        by_language_pair = [
            {
                "source": row[0],
                "target": row[1],
                "count": row[2],
            }
            for row in lang_result.all()
        ]

        # Accuracy estimate: translated messages without reports / total translated
        translated_count = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.clinic_id == clinic_id,
                Message.translated_content.isnot(None),
                func.date(Message.created_at) >= cutoff,
            )
        )
        total_translated = translated_count.scalar() or 0
        accuracy_score = None
        if total_translated > 0:
            accuracy_score = round(
                (1 - total_reports / total_translated) * 100, 1
            )

        return {
            "total_reports": total_reports,
            "pending_count": status_counts.get("pending", 0),
            "resolved_count": status_counts.get("resolved", 0),
            "critical_count": critical_count,
            "by_error_type": by_error_type,
            "by_language_pair": by_language_pair,
            "accuracy_score": accuracy_score,
        }

    async def delete_report(
        self, report_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> None:
        result = await self.db.execute(
            select(TranslationReport).where(
                TranslationReport.id == report_id,
                TranslationReport.clinic_id == clinic_id,
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise NotFoundError("Translation report not found")
        await self.db.delete(report)
        await self.db.flush()
