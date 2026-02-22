import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.treatment_photo import (
    TreatmentPhotoResponse,
    TreatmentPhotoUpdate,
)
from app.services.storage_service import ALLOWED_IMAGE_TYPES, storage_service
from app.services.treatment_photo_service import TreatmentPhotoService

router = APIRouter(prefix="/treatment-photos", tags=["treatment-photos"])


@router.post("/upload", response_model=TreatmentPhotoResponse, status_code=201)
async def upload_treatment_photo(
    file: UploadFile = File(...),
    customer_id: uuid.UUID = Form(...),
    photo_type: str = Form(...),  # before / after / progress
    booking_id: uuid.UUID | None = Form(None),
    procedure_id: uuid.UUID | None = Form(None),
    description: str | None = Form(None),
    days_after_procedure: int | None = Form(None),
    is_consent_given: bool = Form(False),
    pair_id: uuid.UUID | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a before/after treatment photo."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}")

    file_data = await file.read()
    url = await storage_service.upload(
        file_data,
        file.filename or "photo.jpg",
        file.content_type or "image/jpeg",
        current_user.clinic_id,
        category="treatment-photos",
    )

    svc = TreatmentPhotoService(db)
    photo = await svc.create_photo(
        clinic_id=current_user.clinic_id,
        photo_url=url,
        thumbnail_url=None,
        customer_id=customer_id,
        photo_type=photo_type,
        booking_id=booking_id,
        procedure_id=procedure_id,
        description=description,
        days_after_procedure=days_after_procedure,
        is_consent_given=is_consent_given,
        pair_id=pair_id,
    )
    await db.commit()
    return photo


@router.get("/")
async def list_treatment_photos(
    customer_id: uuid.UUID | None = Query(None),
    booking_id: uuid.UUID | None = Query(None),
    photo_type: str | None = Query(None),
    portfolio_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TreatmentPhotoService(db)
    photos, total = await svc.list_photos(
        clinic_id=current_user.clinic_id,
        customer_id=customer_id,
        booking_id=booking_id,
        photo_type=photo_type,
        portfolio_only=portfolio_only,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [TreatmentPhotoResponse.model_validate(p) for p in photos],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/pairs")
async def list_photo_pairs(
    customer_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get before/after photo pairs."""
    svc = TreatmentPhotoService(db)
    pairs = await svc.get_pairs(
        clinic_id=current_user.clinic_id,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )
    result = []
    for pair in pairs:
        result.append({
            "pair_id": str(pair["pair_id"]),
            "before": TreatmentPhotoResponse.model_validate(pair["before"]) if pair["before"] else None,
            "after": TreatmentPhotoResponse.model_validate(pair["after"]) if pair["after"] else None,
        })
    return result


@router.get("/{photo_id}", response_model=TreatmentPhotoResponse)
async def get_treatment_photo(
    photo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TreatmentPhotoService(db)
    return await svc.get_photo(photo_id, current_user.clinic_id)


@router.patch("/{photo_id}", response_model=TreatmentPhotoResponse)
async def update_treatment_photo(
    photo_id: uuid.UUID,
    body: TreatmentPhotoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TreatmentPhotoService(db)
    photo = await svc.update_photo(
        photo_id,
        current_user.clinic_id,
        **body.model_dump(exclude_none=True),
    )
    await db.commit()
    return photo


@router.post("/{photo_id}/approve", response_model=TreatmentPhotoResponse)
async def approve_photo(
    photo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a photo for portfolio use."""
    svc = TreatmentPhotoService(db)
    photo = await svc.approve_for_portfolio(
        photo_id, current_user.clinic_id, current_user.id
    )
    await db.commit()
    return photo


@router.delete("/{photo_id}", status_code=204)
async def delete_treatment_photo(
    photo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TreatmentPhotoService(db)
    await svc.delete_photo(photo_id, current_user.clinic_id)
    await db.commit()
