"""LangChain tools for the AI consultation agent.

Each tool is bound to a specific DB session, clinic, and customer context.
"""

import uuid
from datetime import date, time

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.retriever import VectorRetriever
from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.conversation import Conversation


def create_consultation_tools(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    customer_id: uuid.UUID,
    conversation_id: uuid.UUID,
):
    """Create a set of tools bound to the current DB session and context."""

    @tool
    async def search_procedures(query: str) -> str:
        """Search clinic's procedure catalog by name or description.
        Use when the customer asks about available procedures, treatments, or services.
        """
        retriever = VectorRetriever(db)
        results = await retriever.search_procedures(clinic_id, query, limit=5)

        if not results:
            return "검색 결과가 없습니다."

        lines = []
        for p in results:
            line = f"- {p.name_ko}"
            if p.name_en:
                line += f" ({p.name_en})"
            if p.description_ko:
                line += f": {p.description_ko}"
            if p.duration_minutes:
                line += f" (시술시간: {p.duration_minutes}분)"
            lines.append(line)
        return "\n".join(lines)

    @tool
    async def create_booking(procedure_name: str, booking_date: str, booking_time: str) -> str:
        """Create a booking for the customer.
        Use when the customer confirms they want to book a procedure on a specific date and time.
        Args:
            procedure_name: Name of the procedure to book
            booking_date: Date in YYYY-MM-DD format
            booking_time: Time in HH:MM format
        """
        from app.models.clinic_procedure import ClinicProcedure
        from app.models.procedure import Procedure

        # Find the procedure
        result = await db.execute(
            select(ClinicProcedure)
            .join(Procedure)
            .where(
                ClinicProcedure.clinic_id == clinic_id,
                ClinicProcedure.is_active.is_(True),
                Procedure.name_ko.ilike(f"%{procedure_name}%"),
            )
            .limit(1)
        )
        cp = result.scalar_one_or_none()
        if cp is None:
            return f"'{procedure_name}' 시술을 찾을 수 없습니다."

        try:
            b_date = date.fromisoformat(booking_date)
            b_time = time.fromisoformat(booking_time)
        except ValueError:
            return "날짜 또는 시간 형식이 올바르지 않습니다. (YYYY-MM-DD, HH:MM)"

        booking = Booking(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            clinic_procedure_id=cp.id,
            booking_date=b_date,
            booking_time=b_time,
            status="pending",
        )
        db.add(booking)
        await db.flush()
        return f"예약이 완료되었습니다: {procedure_name} {booking_date} {booking_time}"

    @tool
    async def send_payment_link(booking_id: str) -> str:
        """Send a payment link for a booking.
        Use when the customer is ready to pay for their booking.
        """
        from app.services.payment_service import PaymentService

        try:
            bid = uuid.UUID(booking_id)
        except ValueError:
            return "잘못된 예약 ID입니다."

        result = await db.execute(
            select(Booking).where(Booking.id == bid, Booking.clinic_id == clinic_id)
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            return "예약을 찾을 수 없습니다."

        svc = PaymentService(db)
        payment = await svc.create_payment_link(
            clinic_id=clinic_id,
            booking_id=bid,
            customer_id=customer_id,
            payment_type="deposit",
            amount=float(booking.deposit_amount or booking.total_amount or 0),
            currency=booking.currency or "KRW",
        )
        return f"결제 링크가 전송되었습니다: {payment.payment_link}"

    @tool
    async def check_availability(check_date: str) -> str:
        """Check available time slots for a given date.
        Use when the customer asks about available times.
        Args:
            check_date: Date in YYYY-MM-DD format
        """
        try:
            date.fromisoformat(check_date)
        except ValueError:
            return "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)"

        # MVP: return fixed slots 10:00~17:00, 1-hour intervals
        slots = [f"{h:02d}:00" for h in range(10, 18)]
        return f"{check_date} 예약 가능 시간: {', '.join(slots)}"

    @tool
    async def escalate_to_human(reason: str) -> str:
        """Escalate the conversation to a human staff member.
        Use when the customer explicitly requests a human, or the issue is beyond AI capability.
        Args:
            reason: Reason for escalation
        """
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.ai_mode = False
            conv.status = "waiting"
            await db.flush()
        return f"상담사 연결 중입니다. 사유: {reason}"

    @tool
    async def get_clinic_info() -> str:
        """Get clinic's basic information.
        Use when the customer asks about the clinic's location, hours, or contact info.
        """
        result = await db.execute(
            select(Clinic).where(Clinic.id == clinic_id)
        )
        clinic = result.scalar_one_or_none()
        if clinic is None:
            return "클리닉 정보를 찾을 수 없습니다."

        lines = [f"클리닉: {clinic.name}"]
        if clinic.address:
            lines.append(f"주소: {clinic.address}")
        if clinic.phone:
            lines.append(f"전화: {clinic.phone}")
        if clinic.email:
            lines.append(f"이메일: {clinic.email}")
        return "\n".join(lines)

    return [
        search_procedures,
        create_booking,
        send_payment_link,
        check_availability,
        escalate_to_human,
        get_clinic_info,
    ]
