import copy

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.clinic import Clinic
from app.models.user import User
from app.schemas.payment_settings import PaymentSettingsResponse, PaymentSettingsUpdate

router = APIRouter(prefix="/payment-settings", tags=["payment-settings"])


@router.get("", response_model=PaymentSettingsResponse)
async def get_payment_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Clinic).where(Clinic.id == current_user.clinic_id)
    )
    clinic = result.scalar_one()
    return clinic.settings.get("payment", {})


@router.patch("", response_model=PaymentSettingsResponse)
async def update_payment_settings(
    body: PaymentSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Clinic).where(Clinic.id == current_user.clinic_id)
    )
    clinic = result.scalar_one()

    # Merge update into existing settings (deep copy to trigger JSONB change detection)
    current = copy.deepcopy(clinic.settings)
    payment = current.get("payment", {})
    update_data = body.model_dump(exclude_unset=True)
    payment.update(update_data)
    current["payment"] = payment
    clinic.settings = current

    await db.flush()
    await db.refresh(clinic)
    return clinic.settings.get("payment", {})
