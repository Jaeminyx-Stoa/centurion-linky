import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.pagination import paginate
from app.dependencies import get_current_user, get_pagination
from app.models.package_enrollment import PackageEnrollment
from app.models.procedure_package import ProcedurePackage
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.procedure_package import (
    PackageEnrollmentCreate,
    PackageEnrollmentResponse,
    ProcedurePackageCreate,
    ProcedurePackageResponse,
    ProcedurePackageUpdate,
)
from app.services.package_service import PackageService

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("", response_model=ProcedurePackageResponse, status_code=201)
async def create_package(
    body: ProcedurePackageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    package = ProcedurePackage(
        id=uuid.uuid4(),
        clinic_id=current_user.clinic_id,
        **body.model_dump(),
    )
    # Serialize items to JSONB-friendly format
    if body.items:
        package.items = [item.model_dump(mode="json") for item in body.items]
    db.add(package)
    await db.flush()
    return package


@router.get("")
async def list_packages(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ProcedurePackageResponse]:
    stmt = (
        select(ProcedurePackage)
        .where(ProcedurePackage.clinic_id == current_user.clinic_id)
        .order_by(ProcedurePackage.created_at.desc())
    )
    return await paginate(db, stmt, pagination)


@router.get("/{package_id}", response_model=ProcedurePackageResponse)
async def get_package(
    package_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcedurePackage).where(
            ProcedurePackage.id == package_id,
            ProcedurePackage.clinic_id == current_user.clinic_id,
        )
    )
    package = result.scalar_one_or_none()
    if package is None:
        raise NotFoundError("Package not found")
    return package


@router.patch("/{package_id}", response_model=ProcedurePackageResponse)
async def update_package(
    package_id: uuid.UUID,
    body: ProcedurePackageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcedurePackage).where(
            ProcedurePackage.id == package_id,
            ProcedurePackage.clinic_id == current_user.clinic_id,
        )
    )
    package = result.scalar_one_or_none()
    if package is None:
        raise NotFoundError("Package not found")

    update_data = body.model_dump(exclude_unset=True)
    if "items" in update_data and update_data["items"] is not None:
        update_data["items"] = [item.model_dump(mode="json") for item in body.items]
    for field, value in update_data.items():
        setattr(package, field, value)
    await db.flush()
    return package


@router.post("/{package_id}/enroll", response_model=PackageEnrollmentResponse)
async def enroll_customer(
    package_id: uuid.UUID,
    body: PackageEnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PackageService(db)
    enrollment = await svc.create_enrollment(
        package_id, body.customer_id, current_user.clinic_id
    )
    # Reload with sessions
    result = await db.execute(
        select(PackageEnrollment)
        .options(selectinload(PackageEnrollment.sessions))
        .where(PackageEnrollment.id == enrollment.id)
    )
    return result.scalar_one()


@router.get("/{package_id}/enrollments")
async def list_enrollments(
    package_id: uuid.UUID,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PackageEnrollmentResponse]:
    stmt = (
        select(PackageEnrollment)
        .options(selectinload(PackageEnrollment.sessions))
        .where(
            PackageEnrollment.package_id == package_id,
            PackageEnrollment.clinic_id == current_user.clinic_id,
        )
        .order_by(PackageEnrollment.created_at.desc())
    )
    return await paginate(db, stmt, pagination)


@router.get("/enrollments/{enrollment_id}", response_model=PackageEnrollmentResponse)
async def get_enrollment(
    enrollment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PackageEnrollment)
        .options(selectinload(PackageEnrollment.sessions))
        .where(
            PackageEnrollment.id == enrollment_id,
            PackageEnrollment.clinic_id == current_user.clinic_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        raise NotFoundError("Enrollment not found")
    return enrollment


@router.post("/enrollments/{enrollment_id}/sessions/{session_number}/complete")
async def complete_session(
    enrollment_id: uuid.UUID,
    session_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PackageService(db)
    session = await svc.complete_session(
        enrollment_id, session_number, current_user.clinic_id
    )
    return {"status": "ok", "session_number": session.session_number}
