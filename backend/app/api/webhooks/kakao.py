"""Webhook endpoint for KakaoTalk Channel API.

POST /api/webhooks/kakao/{account_id} — Incoming KakaoTalk chatbot events
"""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.messenger.kakao import KakaoAdapter
from app.models.messenger_account import MessengerAccount
from app.services.message_service import MessageService

router = APIRouter(prefix="/webhooks/kakao", tags=["webhooks"])

adapter = KakaoAdapter()


@router.post("/{account_id}")
async def kakao_webhook(
    account_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming KakaoTalk webhook events."""
    result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise NotFoundError("Messenger account not found")
    if not account.is_active:
        raise PermissionDeniedError("Messenger account is inactive")

    # Verify token
    body = await request.body()
    headers = dict(request.headers)

    is_valid = await adapter.verify_webhook(body, headers, secret=account.webhook_secret)
    if not is_valid:
        raise PermissionDeniedError("Invalid webhook verification")

    # Parse and process
    payload = await request.json()
    messages = await adapter.parse_webhook(account, payload)

    message_service = MessageService(db)
    for msg in messages:
        await message_service.process_incoming(msg)

    return {"status": "ok"}
