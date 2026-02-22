import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.medical_document import MedicalDocument
from app.models.user import User
from app.schemas.medical_document import (
    DocumentGenerateRequest,
    DocumentStatusUpdate,
    MedicalDocumentResponse,
)
from app.services.medical_document_service import MedicalDocumentService

router = APIRouter(prefix="/medical-documents", tags=["medical-documents"])


@router.post(
    "/generate/chart-draft",
    response_model=MedicalDocumentResponse,
    status_code=201,
)
async def generate_chart_draft(
    body: DocumentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.conversation_id:
        raise NotFoundError("conversation_id is required")
    svc = MedicalDocumentService(db)
    doc = await svc.generate_chart_draft(
        body.conversation_id, current_user.clinic_id
    )
    return _doc_to_response(doc)


@router.post(
    "/generate/consent-form",
    response_model=MedicalDocumentResponse,
    status_code=201,
)
async def generate_consent_form(
    body: DocumentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.booking_id:
        raise NotFoundError("booking_id is required")
    svc = MedicalDocumentService(db)
    doc = await svc.generate_consent_form(
        body.booking_id, current_user.clinic_id, body.language
    )
    return _doc_to_response(doc)


@router.get("/")
async def list_medical_documents(
    customer_id: uuid.UUID | None = Query(None),
    booking_id: uuid.UUID | None = Query(None),
    document_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MedicalDocumentService(db)
    docs, total = await svc.list_documents(
        clinic_id=current_user.clinic_id,
        customer_id=customer_id,
        booking_id=booking_id,
        document_type=document_type,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_doc_to_response(d) for d in docs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{document_id}", response_model=MedicalDocumentResponse)
async def get_medical_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(MedicalDocument)
        .options(selectinload(MedicalDocument.customer))
        .where(
            MedicalDocument.id == document_id,
            MedicalDocument.clinic_id == current_user.clinic_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise NotFoundError("Medical document not found")
    return _doc_to_response(doc)


@router.patch("/{document_id}/status", response_model=MedicalDocumentResponse)
async def update_document_status(
    document_id: uuid.UUID,
    body: DocumentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MedicalDocumentService(db)
    doc = await svc.update_status(
        document_id=document_id,
        clinic_id=current_user.clinic_id,
        status=body.status,
        reviewer_id=current_user.id,
    )
    return _doc_to_response(doc)


@router.delete("/{document_id}", status_code=204)
async def delete_medical_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(
        select(MedicalDocument).where(
            MedicalDocument.id == document_id,
            MedicalDocument.clinic_id == current_user.clinic_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise NotFoundError("Medical document not found")
    await db.delete(doc)
    await db.flush()


def _doc_to_response(doc: MedicalDocument) -> MedicalDocumentResponse:
    customer_name = None
    if hasattr(doc, "customer") and doc.customer:
        customer_name = doc.customer.name
    return MedicalDocumentResponse(
        id=doc.id,
        clinic_id=doc.clinic_id,
        customer_id=doc.customer_id,
        customer_name=customer_name,
        booking_id=doc.booking_id,
        conversation_id=doc.conversation_id,
        document_type=doc.document_type,
        title=doc.title,
        content=doc.content,
        language=doc.language,
        status=doc.status,
        generated_by=doc.generated_by,
        reviewed_by=doc.reviewed_by,
        reviewed_at=doc.reviewed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )
