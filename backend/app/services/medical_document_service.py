import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.booking import Booking
from app.models.clinic_procedure import ClinicProcedure
from app.models.conversation import Conversation
from app.models.medical_document import MedicalDocument
from app.models.message import Message
from app.models.procedure import Procedure

logger = logging.getLogger(__name__)

CHART_DRAFT_PROMPT = """You are a medical chart assistant. Extract clinical information from the following consultation conversation.
Return a JSON object with these fields:
- chief_complaint: patient's main concern
- desired_procedures: list of procedures the patient is interested in
- medical_history: relevant medical history mentioned
- allergies: any allergies mentioned
- medications: any medications mentioned
- skin_type: skin type if mentioned
- ai_recommendations: your clinical recommendations
- notes: any other relevant notes

Conversation:
{conversation}

Return ONLY valid JSON, no other text."""

CONSENT_FORM_PROMPT = """Generate a medical consent form in {language} for the following procedure.
Return a JSON object with:
- procedure_name: name of the procedure
- procedure_description: description of the procedure
- risks: list of potential risks and side effects
- alternatives: alternative treatment options
- expected_results: expected outcomes
- aftercare_instructions: post-procedure care instructions
- patient_acknowledgements: list of statements the patient acknowledges

Procedure information:
Name: {procedure_name}
Description: {procedure_description}
Side effects: {side_effects}
Precautions after: {precautions_after}
Recovery period: {recovery_days} days

Return ONLY valid JSON, no other text."""


class MedicalDocumentService:
    """Generates and manages medical documents (chart drafts, consent forms)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_chart_draft(
        self,
        conversation_id: uuid.UUID,
        clinic_id: uuid.UUID,
    ) -> MedicalDocument:
        """Extract clinical information from conversation and create a chart draft."""
        # Load conversation
        conv_result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.clinic_id == clinic_id,
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation is None:
            raise NotFoundError("Conversation not found")

        # Load messages
        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(50)
        )
        messages = msg_result.scalars().all()

        conversation_text = "\n".join(
            f"{'고객' if m.sender_type == 'customer' else 'AI'}: {m.content or ''}"
            for m in messages
        )

        # Call LLM for extraction
        prompt = CHART_DRAFT_PROMPT.format(conversation=conversation_text)
        content = await self._call_llm(prompt)

        doc = MedicalDocument(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            customer_id=conversation.customer_id,
            conversation_id=conversation_id,
            document_type="chart_draft",
            title=f"Chart Draft - {conversation_id}",
            content=content,
            language="ko",
            status="draft",
            generated_by="ai",
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def generate_consent_form(
        self,
        booking_id: uuid.UUID,
        clinic_id: uuid.UUID,
        language: str = "ko",
    ) -> MedicalDocument:
        """Generate a consent form for a booking's procedure."""
        # Load booking with procedure
        booking_result = await self.db.execute(
            select(Booking)
            .options(
                selectinload(Booking.clinic_procedure).selectinload(
                    ClinicProcedure.procedure
                )
            )
            .where(Booking.id == booking_id, Booking.clinic_id == clinic_id)
        )
        booking = booking_result.scalar_one_or_none()
        if booking is None:
            raise NotFoundError("Booking not found")

        procedure_name = "Unknown Procedure"
        procedure_description = ""
        side_effects = ""
        precautions_after = ""
        recovery_days = 0

        if booking.clinic_procedure and booking.clinic_procedure.procedure:
            proc: Procedure = booking.clinic_procedure.procedure
            procedure_name = proc.name_ko or procedure_name
            procedure_description = proc.description_ko or ""
            side_effects = proc.common_side_effects or ""
            precautions_after = (
                booking.clinic_procedure.custom_precautions_after
                or proc.precautions_after
                or ""
            )
            recovery_days = (
                booking.clinic_procedure.custom_downtime_days
                or proc.downtime_days
                or 0
            )

        prompt = CONSENT_FORM_PROMPT.format(
            language=language,
            procedure_name=procedure_name,
            procedure_description=procedure_description,
            side_effects=side_effects,
            precautions_after=precautions_after,
            recovery_days=recovery_days,
        )
        content = await self._call_llm(prompt)

        doc = MedicalDocument(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            customer_id=booking.customer_id,
            booking_id=booking_id,
            document_type="consent_form",
            title=f"Consent Form - {procedure_name}",
            content=content,
            language=language,
            status="draft",
            generated_by="ai",
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def list_documents(
        self,
        clinic_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
        booking_id: uuid.UUID | None = None,
        document_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MedicalDocument], int]:
        """List medical documents with filters."""
        query = select(MedicalDocument).where(
            MedicalDocument.clinic_id == clinic_id
        )
        count_query = select(func.count(MedicalDocument.id)).where(
            MedicalDocument.clinic_id == clinic_id
        )

        if customer_id:
            query = query.where(MedicalDocument.customer_id == customer_id)
            count_query = count_query.where(
                MedicalDocument.customer_id == customer_id
            )
        if booking_id:
            query = query.where(MedicalDocument.booking_id == booking_id)
            count_query = count_query.where(
                MedicalDocument.booking_id == booking_id
            )
        if document_type:
            query = query.where(MedicalDocument.document_type == document_type)
            count_query = count_query.where(
                MedicalDocument.document_type == document_type
            )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(
            query.options(selectinload(MedicalDocument.customer))
            .order_by(MedicalDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        docs = list(result.scalars().all())
        return docs, total

    async def update_status(
        self,
        document_id: uuid.UUID,
        clinic_id: uuid.UUID,
        status: str,
        reviewer_id: uuid.UUID | None = None,
    ) -> MedicalDocument:
        """Update document review status."""
        result = await self.db.execute(
            select(MedicalDocument).where(
                MedicalDocument.id == document_id,
                MedicalDocument.clinic_id == clinic_id,
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Medical document not found")

        doc.status = status
        if reviewer_id:
            doc.reviewed_by = reviewer_id
            doc.reviewed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return doc

    async def _call_llm(self, prompt: str) -> dict:
        """Call LLM and parse JSON response."""
        try:
            from app.ai.llm_router import get_light_llm

            llm = get_light_llm()
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON response, wrapping as notes")
            return {"notes": content if "content" in dir() else "Generation failed"}
        except Exception:
            logger.exception("LLM call failed for medical document generation")
            return {"notes": "AI generation unavailable"}
