import secrets
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.schemas.messenger import (
    MessengerAccountCreate,
    MessengerAccountResponse,
    MessengerAccountUpdate,
)

router = APIRouter(prefix="/messenger-accounts", tags=["messenger-accounts"])


@router.post("", response_model=MessengerAccountResponse, status_code=201)
async def create_messenger_account(
    body: MessengerAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account_id = uuid.uuid4()
    webhook_secret = secrets.token_urlsafe(32)
    webhook_url = f"/api/webhooks/{body.messenger_type}/{account_id}"

    account = MessengerAccount(
        id=account_id,
        clinic_id=current_user.clinic_id,
        messenger_type=body.messenger_type,
        account_name=body.account_name,
        display_name=body.display_name,
        credentials=body.credentials,
        target_countries=body.target_countries,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
    )
    db.add(account)
    await db.flush()
    return account


@router.get("", response_model=list[MessengerAccountResponse])
async def list_messenger_accounts(
    messenger_type: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(MessengerAccount).where(
        MessengerAccount.clinic_id == current_user.clinic_id
    )
    if messenger_type:
        query = query.where(MessengerAccount.messenger_type == messenger_type)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{account_id}", response_model=MessengerAccountResponse)
async def get_messenger_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(db, account_id, current_user.clinic_id)
    return account


@router.patch("/{account_id}", response_model=MessengerAccountResponse)
async def update_messenger_account(
    account_id: uuid.UUID,
    body: MessengerAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(db, account_id, current_user.clinic_id)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.flush()
    return account


@router.delete("/{account_id}", status_code=204)
async def delete_messenger_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(db, account_id, current_user.clinic_id)
    await db.delete(account)
    await db.flush()


async def _get_account(
    db: AsyncSession, account_id: uuid.UUID, clinic_id: uuid.UUID
) -> MessengerAccount:
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.clinic_id == clinic_id,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise NotFoundError("Messenger account not found")
    return account
