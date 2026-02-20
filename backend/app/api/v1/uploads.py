"""File upload endpoints."""

import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestError
from app.dependencies import get_current_user
from app.models.user import User
from app.services.storage_service import (
    ALLOWED_FILE_TYPES,
    ALLOWED_IMAGE_TYPES,
    MAX_FILE_SIZE,
    storage_service,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/image")
async def upload_image(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image file. Returns the file URL."""
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestError(
            f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise BadRequestError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

    url = await storage_service.upload(
        file_data=data,
        filename=file.filename or "image",
        content_type=file.content_type,
        clinic_id=current_user.clinic_id,
        category="images",
    )
    return {"url": url, "filename": file.filename, "content_type": file.content_type}


@router.post("/file")
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a general file. Returns the file URL."""
    if not file.content_type or file.content_type not in ALLOWED_FILE_TYPES:
        raise BadRequestError(
            f"Invalid file type. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise BadRequestError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

    url = await storage_service.upload(
        file_data=data,
        filename=file.filename or "file",
        content_type=file.content_type,
        clinic_id=current_user.clinic_id,
        category="files",
    )
    return {"url": url, "filename": file.filename, "content_type": file.content_type}
