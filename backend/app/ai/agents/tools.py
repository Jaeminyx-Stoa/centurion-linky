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

    @tool
    async def check_contraindications(procedure_name: str) -> str:
        """Check if the customer has any health contraindications for a procedure.
        Use when the customer asks about a procedure and you need to verify safety.
        Args:
            procedure_name: Name of the procedure to check
        """
        from app.models.clinic_procedure import ClinicProcedure
        from app.models.procedure import Procedure
        from app.services.contraindication_service import ContraindicationService

        # Find the clinic procedure
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

        svc = ContraindicationService(db)
        check_result = await svc.check(customer_id, cp.id, clinic_id)

        if not check_result.has_warnings:
            return f"'{procedure_name}' 시술에 대한 금기사항이 없습니다."

        lines = [f"⚠️ '{procedure_name}' 금기사항 체크 결과:"]
        for w in check_result.warnings:
            prefix = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(
                w.severity, "⚪"
            )
            lines.append(f"{prefix} [{w.category}] {w.detail}")
        return "\n".join(lines)

    @tool
    async def get_protocol_checklist(procedure_name: str) -> str:
        """Get the consultation protocol checklist for a procedure.
        Returns unanswered checklist items that need to be completed.
        Args:
            procedure_name: Name of the procedure
        """
        from app.models.consultation_protocol import ConsultationProtocol
        from app.models.procedure import Procedure

        # Find procedure ID
        proc_result = await db.execute(
            select(Procedure).where(
                Procedure.name_ko.ilike(f"%{procedure_name}%"),
            ).limit(1)
        )
        procedure = proc_result.scalar_one_or_none()
        if procedure is None:
            return f"'{procedure_name}' 시술을 찾을 수 없습니다."

        # Find protocol
        proto_result = await db.execute(
            select(ConsultationProtocol).where(
                ConsultationProtocol.clinic_id == clinic_id,
                ConsultationProtocol.is_active.is_(True),
                (ConsultationProtocol.procedure_id == procedure.id)
                | (ConsultationProtocol.procedure_id.is_(None)),
            ).limit(1)
        )
        protocol = proto_result.scalar_one_or_none()
        if protocol is None:
            return f"'{procedure_name}'에 대한 상담 프로토콜이 없습니다."

        checklist = protocol.checklist_items or []
        if not checklist:
            return "체크리스트 항목이 없습니다."

        lines = [f"📋 '{procedure_name}' 상담 체크리스트:"]
        for item in checklist:
            required = "⚠️ 필수" if item.get("required") else ""
            lines.append(f"- [{item['id']}] {item.get('question_ko', '')} {required}")
        return "\n".join(lines)

    @tool
    async def update_protocol_item(procedure_name: str, item_id: str, answer: str) -> str:
        """Update a protocol checklist item with the customer's answer.
        Args:
            procedure_name: Name of the procedure
            item_id: ID of the checklist item (e.g., 'chk_1')
            answer: Customer's answer
        """
        from app.models.booking import Booking as BookingModel

        # Find booking with protocol_state for this conversation
        booking_result = await db.execute(
            select(BookingModel).where(
                BookingModel.conversation_id == conversation_id,
                BookingModel.clinic_id == clinic_id,
                BookingModel.protocol_state.isnot(None),
            ).limit(1)
        )
        booking = booking_result.scalar_one_or_none()
        if booking is None:
            return "프로토콜 상태가 초기화된 예약을 찾을 수 없습니다."

        state = booking.protocol_state or {}
        items = state.get("items", [])

        updated = False
        for item in items:
            if item["id"] == item_id:
                item["answered"] = True
                item["answer"] = answer
                updated = True
                break

        if not updated:
            return f"체크리스트 항목 '{item_id}'을(를) 찾을 수 없습니다."

        booking.protocol_state = state
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(booking, "protocol_state")
        await db.flush()

        completed = sum(1 for i in items if i.get("answered"))
        return f"항목 '{item_id}' 완료. 진행률: {completed}/{len(items)}"

    return [
        search_procedures,
        create_booking,
        send_payment_link,
        check_availability,
        escalate_to_human,
        get_clinic_info,
        check_contraindications,
        get_protocol_checklist,
        update_protocol_item,
    ]
