"""Webhook endpoints for Meta Platform (Instagram, Facebook, WhatsApp).

GET  /api/webhooks/meta/{account_id} — Meta verification challenge
POST /api/webhooks/meta/{account_id} — Incoming message events
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.messenger.factory import MessengerAdapterFactory
from app.models.messenger_account import MessengerAccount
from app.services.ai_response_background import broadcast_incoming_message
from app.services.message_service import MessageService
from app.tasks.ai_response import generate_ai_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/meta", tags=["webhooks"])


async def _get_account(db: AsyncSession, account_id: uuid.UUID) -> MessengerAccount:
    result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise NotFoundError("Messenger account not found")
    if not account.is_active:
        raise PermissionDeniedError("Messenger account is inactive")
    return account


@router.get("/{account_id}")
async def meta_webhook_verify(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta webhook verification (GET). Returns hub.challenge if token matches."""
    account = await _get_account(db, account_id)

    if hub_mode == "subscribe" and hub_verify_token == account.webhook_secret:
        return Response(content=hub_challenge, media_type="text/plain")

    raise PermissionDeniedError("Invalid verification token")


@router.post("/{account_id}")
async def meta_webhook_post(
    account_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Meta webhook events (Instagram, Facebook, WhatsApp)."""
    account = await _get_account(db, account_id)

    # Verify HMAC-SHA256 signature
    body = await request.body()
    headers = dict(request.headers)
    app_secret = account.credentials.get("app_secret", "")

    adapter = MessengerAdapterFactory.get_adapter(account.messenger_type)
    is_valid = await adapter.verify_webhook(body, headers, secret=app_secret)
    if not is_valid:
        raise PermissionDeniedError("Invalid webhook signature")

    # Parse and process
    payload = await request.json()
    messages = await adapter.parse_webhook(account, payload)

    message_service = MessageService(db)
    processed = 0
    failed = 0
    for msg in messages:
        try:
            processing_result = await message_service.process_incoming(msg)

            # Broadcast incoming message to staff dashboard
            await broadcast_incoming_message(
                processing_result.message, account.clinic_id
            )

            # Queue AI auto-response via Celery
            if msg.content_type == "text" and msg.content:
                generate_ai_response.delay(
                    message_id=str(processing_result.message.id),
                    conversation_id=str(processing_result.conversation.id),
                    idempotency_key=f"meta-{processing_result.message.id}",
                )
            processed += 1
        except Exception:
            failed += 1
            logger.exception(
                "Meta webhook message processing failed: "
                "provider=%s account_id=%s messenger_user=%s",
                account.messenger_type,
                account_id,
                msg.messenger_user_id,
            )

    logger.info(
        "Meta webhook processed: provider=%s account_id=%s processed=%d failed=%d",
        account.messenger_type,
        account_id,
        processed,
        failed,
    )
    return {"status": "ok"}
