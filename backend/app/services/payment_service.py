import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.booking import Booking
from app.models.payment import Payment
from app.payment.base import PaymentResult
from app.payment.factory import PaymentProviderFactory


class PaymentService:
    """Orchestrates payment creation, webhook handling, and booking status updates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_link(
        self,
        clinic_id: uuid.UUID,
        booking_id: uuid.UUID | None,
        customer_id: uuid.UUID,
        payment_type: str,
        amount: float,
        currency: str,
        provider_type: str | None = None,
    ) -> Payment:
        """Create a payment record and generate a payment link."""
        if provider_type:
            pg_type = provider_type
            provider = PaymentProviderFactory.get_provider(provider_type)
        else:
            pg_type, provider = PaymentProviderFactory.get_provider_for()

        link_result = await provider.create_payment_link(
            amount=amount, currency=currency, metadata={"clinic_id": str(clinic_id)}
        )

        payment = Payment(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            booking_id=booking_id,
            customer_id=customer_id,
            payment_type=payment_type,
            amount=amount,
            currency=currency,
            pg_provider=pg_type,
            pg_payment_id=link_result.provider_payment_id,
            payment_link=link_result.link,
            qr_code_url=link_result.qr_url,
            link_expires_at=link_result.expires_at,
            status="link_sent",
        )
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def handle_webhook(
        self, provider_type: str, payment_result: PaymentResult
    ) -> Payment:
        """Process a webhook callback from a PG provider. Idempotent."""
        result = await self.db.execute(
            select(Payment).where(
                Payment.pg_payment_id == payment_result.provider_payment_id
            )
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            raise NotFoundError("Payment not found for provider payment ID")

        # Idempotent: already completed → return as-is
        if payment.status == "completed":
            return payment

        payment.status = payment_result.status
        payment.payment_method = payment_result.payment_method
        payment.paid_at = payment_result.paid_at

        # If payment completed, confirm the linked booking
        if payment_result.status == "completed" and payment.booking_id:
            booking_result = await self.db.execute(
                select(Booking).where(Booking.id == payment.booking_id)
            )
            booking = booking_result.scalar_one_or_none()
            if booking and booking.status == "pending":
                booking.status = "confirmed"

        await self.db.flush()
        return payment

    async def request_remaining(
        self,
        clinic_id: uuid.UUID,
        booking_id: uuid.UUID,
        customer_id: uuid.UUID,
        amount: float,
        currency: str,
    ) -> Payment:
        """Create a payment for the remaining balance of a booking."""
        # Validate booking exists and is confirmed
        result = await self.db.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.clinic_id == clinic_id,
            )
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.status != "confirmed":
            raise BadRequestError("Booking must be confirmed to request remaining payment")

        return await self.create_payment_link(
            clinic_id=clinic_id,
            booking_id=booking_id,
            customer_id=customer_id,
            payment_type="remaining",
            amount=amount,
            currency=currency,
        )
