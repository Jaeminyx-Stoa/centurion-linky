from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError
from app.payment.factory import PaymentProviderFactory
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/webhooks/payments", tags=["payment-webhooks"])


async def _handle_provider_webhook(
    provider_type: str, request: Request, db: AsyncSession
) -> dict:
    """Common webhook processing: verify → parse → service.handle_webhook."""
    provider = PaymentProviderFactory.get_provider(provider_type)

    body = await request.body()
    headers = dict(request.headers)

    is_valid = await provider.verify_webhook(body, headers)
    if not is_valid:
        raise PermissionDeniedError("Invalid webhook signature")

    payload = await request.json()
    payment_result = await provider.parse_webhook(payload)

    service = PaymentService(db)
    payment = await service.handle_webhook(provider_type, payment_result)
    return {"status": "ok", "payment_id": str(payment.id)}


@router.post("/kingorder")
async def kingorder_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await _handle_provider_webhook("kingorder", request, db)


@router.post("/alipay")
async def alipay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await _handle_provider_webhook("alipay", request, db)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await _handle_provider_webhook("stripe", request, db)
