import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.translation_report import (
    TranslationReportCreate,
    TranslationReportResponse,
    TranslationReportReview,
)
from app.services.translation_report_service import TranslationReportService

router = APIRouter(prefix="/translation-reports", tags=["translation-qa"])


@router.post("/", response_model=TranslationReportResponse, status_code=201)
async def create_report(
    body: TranslationReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a translation error."""
    svc = TranslationReportService(db)
    report = await svc.create_report(
        clinic_id=current_user.clinic_id,
        reported_by=current_user.id,
        **body.model_dump(),
    )
    await db.commit()
    return report


@router.get("/")
async def list_reports(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TranslationReportService(db)
    reports, total = await svc.list_reports(
        clinic_id=current_user.clinic_id,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [TranslationReportResponse.model_validate(r) for r in reports],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_qa_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get translation QA statistics and accuracy metrics."""
    svc = TranslationReportService(db)
    return await svc.get_qa_stats(current_user.clinic_id, days)


@router.patch("/{report_id}/review", response_model=TranslationReportResponse)
async def review_report(
    report_id: uuid.UUID,
    body: TranslationReportReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Review/resolve a translation report."""
    svc = TranslationReportService(db)
    report = await svc.review_report(
        report_id=report_id,
        clinic_id=current_user.clinic_id,
        reviewer_id=current_user.id,
        status=body.status,
        reviewer_notes=body.reviewer_notes,
        corrected_text=body.corrected_text,
    )
    await db.commit()
    return report


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TranslationReportService(db)
    await svc.delete_report(report_id, current_user.clinic_id)
    await db.commit()
