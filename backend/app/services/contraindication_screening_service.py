"""Real-time contraindication auto-screening during AI chat.

Extracts health mentions from incoming messages via LLM,
updates customer health data, and checks against procedure contraindications.
"""

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic_procedure import ClinicProcedure
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.procedure import Procedure
from app.services.contraindication_service import ContraindicationService

logger = logging.getLogger(__name__)

HEALTH_EXTRACT_PROMPT = """You are a medical screening assistant. Analyze the following patient message for any health-related mentions.

Extract ONLY items that are explicitly stated. Do NOT infer or guess.

Patient message: {message}

Return a JSON object with these fields (use empty lists if nothing found):
- conditions: list of medical conditions mentioned (e.g., "pregnancy", "diabetes", "keloid")
- allergies: list of allergies mentioned (e.g., "lidocaine", "penicillin")
- medications: list of medications mentioned (e.g., "aspirin", "warfarin", "blood thinners")
- mentioned_procedures: list of procedure names mentioned (e.g., "botox", "filler")

Return ONLY valid JSON, no other text."""


class ContraindicationScreeningService:
    """Auto-screens incoming messages for contraindication risks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def screen_message(
        self,
        message_content: str,
        conversation_id: uuid.UUID,
        clinic_id: uuid.UUID,
    ) -> dict | None:
        """Screen a message for health mentions and check contraindications.

        Returns alert dict if critical/warning contraindictions found, None otherwise.
        """
        # Extract health mentions via LLM
        extracted = await self._extract_health_mentions(message_content)
        if not extracted:
            return None

        has_health_data = (
            extracted.get("conditions")
            or extracted.get("allergies")
            or extracted.get("medications")
        )
        if not has_health_data:
            return None

        # Load conversation to get customer
        conv_result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.clinic_id == clinic_id,
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            return None

        # Update customer health data
        customer = await self._update_customer_health(
            conversation.customer_id, clinic_id, extracted
        )
        if not customer:
            return None

        # Find relevant procedures to check against
        warnings = await self._check_against_procedures(
            customer, clinic_id, extracted.get("mentioned_procedures", [])
        )

        if not warnings:
            return None

        return {
            "type": "contraindication_alert",
            "conversation_id": str(conversation_id),
            "customer_id": str(customer.id),
            "customer_name": customer.name or customer.display_name,
            "extracted_health": {
                "conditions": extracted.get("conditions", []),
                "allergies": extracted.get("allergies", []),
                "medications": extracted.get("medications", []),
            },
            "warnings": warnings,
            "critical_count": sum(1 for w in warnings if w["severity"] == "critical"),
            "warning_count": sum(1 for w in warnings if w["severity"] == "warning"),
        }

    async def _extract_health_mentions(self, message: str) -> dict | None:
        """Use LLM to extract health information from message."""
        try:
            from app.ai.llm_router import get_light_llm

            llm = get_light_llm()
            prompt = HEALTH_EXTRACT_PROMPT.format(message=message)
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON for health extraction")
            return None
        except Exception:
            logger.exception("Health mention extraction failed")
            return None

    async def _update_customer_health(
        self,
        customer_id: uuid.UUID,
        clinic_id: uuid.UUID,
        extracted: dict,
    ) -> Customer | None:
        """Merge extracted health data into customer record."""
        result = await self.db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.clinic_id == clinic_id,
            )
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return None

        # Merge conditions
        if extracted.get("conditions"):
            existing = customer.medical_conditions or {"items": []}
            existing_names = {
                item["name"].lower()
                for item in existing.get("items", [])
                if isinstance(item, dict) and "name" in item
            }
            for cond in extracted["conditions"]:
                if cond.lower() not in existing_names:
                    existing.setdefault("items", []).append(
                        {"name": cond, "source": "ai_extracted"}
                    )
            customer.medical_conditions = existing

        # Merge allergies
        if extracted.get("allergies"):
            existing = customer.allergies or {"items": []}
            existing_names = {
                item["name"].lower()
                for item in existing.get("items", [])
                if isinstance(item, dict) and "name" in item
            }
            for allergy in extracted["allergies"]:
                if allergy.lower() not in existing_names:
                    existing.setdefault("items", []).append(
                        {"name": allergy, "source": "ai_extracted"}
                    )
            customer.allergies = existing

        # Merge medications
        if extracted.get("medications"):
            existing = customer.medications or {"items": []}
            existing_names = {
                item["name"].lower()
                for item in existing.get("items", [])
                if isinstance(item, dict) and "name" in item
            }
            for med in extracted["medications"]:
                if med.lower() not in existing_names:
                    existing.setdefault("items", []).append(
                        {"name": med, "source": "ai_extracted"}
                    )
            customer.medications = existing

        await self.db.flush()
        return customer

    async def _check_against_procedures(
        self,
        customer: Customer,
        clinic_id: uuid.UUID,
        mentioned_procedures: list[str],
    ) -> list[dict]:
        """Check customer health data against relevant procedures."""
        warnings = []
        contra_svc = ContraindicationService(self.db)

        # Get clinic procedures to check
        # If specific procedures mentioned, find those; otherwise check recent bookings
        clinic_procedure_ids = []

        if mentioned_procedures:
            for proc_name in mentioned_procedures:
                result = await self.db.execute(
                    select(ClinicProcedure.id)
                    .join(Procedure, ClinicProcedure.procedure_id == Procedure.id)
                    .where(
                        ClinicProcedure.clinic_id == clinic_id,
                        Procedure.name_ko.ilike(f"%{proc_name}%"),
                    )
                    .limit(1)
                )
                cp_id = result.scalar_one_or_none()
                if cp_id:
                    clinic_procedure_ids.append(cp_id)

        # Also check recent bookings if no procedures mentioned
        if not clinic_procedure_ids:
            booking_result = await self.db.execute(
                select(Booking.clinic_procedure_id)
                .where(
                    Booking.clinic_id == clinic_id,
                    Booking.customer_id == customer.id,
                    Booking.status.in_(["pending", "confirmed"]),
                    Booking.clinic_procedure_id.isnot(None),
                )
                .order_by(Booking.created_at.desc())
                .limit(3)
            )
            clinic_procedure_ids = [
                row[0] for row in booking_result.all() if row[0]
            ]

        # Run contraindication check for each procedure
        for cp_id in clinic_procedure_ids:
            check_result = await contra_svc.check(customer.id, cp_id, clinic_id)
            if check_result.has_warnings:
                for w in check_result.warnings:
                    warnings.append({
                        "severity": w.severity,
                        "category": w.category,
                        "procedure_name": w.procedure_name,
                        "detail": w.detail,
                        "matched_item": w.matched_customer_item,
                    })

        return warnings
