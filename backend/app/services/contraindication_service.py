"""Contraindication checking service.

Cross-matches customer health data (conditions, allergies, medications)
against procedure contraindications to detect potential risks.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic_procedure import ClinicProcedure
from app.models.customer import Customer
from app.models.procedure import Procedure
from app.schemas.contraindication import (
    ContraindicationCheckResponse,
    ContraindicationWarning,
)


class ContraindicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(
        self,
        customer_id: uuid.UUID,
        clinic_procedure_id: uuid.UUID,
        clinic_id: uuid.UUID,
    ) -> ContraindicationCheckResponse:
        # Load customer health data
        cust_result = await self.db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.clinic_id == clinic_id,
            )
        )
        customer = cust_result.scalar_one_or_none()
        if customer is None:
            return self._empty_response()

        # Load procedure via clinic_procedure
        cp_result = await self.db.execute(
            select(ClinicProcedure).where(
                ClinicProcedure.id == clinic_procedure_id,
                ClinicProcedure.clinic_id == clinic_id,
            )
        )
        cp = cp_result.scalar_one_or_none()
        if cp is None:
            return self._empty_response()

        proc_result = await self.db.execute(
            select(Procedure).where(Procedure.id == cp.procedure_id)
        )
        procedure = proc_result.scalar_one_or_none()
        if procedure is None:
            return self._empty_response()

        contraindications = procedure.contraindications or {}
        procedure_name = procedure.name_ko

        warnings: list[ContraindicationWarning] = []

        # Check conditions
        contra_conditions = [
            c.lower() for c in contraindications.get("conditions", [])
        ]
        customer_conditions = self._extract_items(customer.medical_conditions)
        for item_name in customer_conditions:
            if item_name.lower() in contra_conditions:
                severity = self._determine_severity(
                    item_name, procedure.dangerous_side_effects
                )
                warnings.append(
                    ContraindicationWarning(
                        severity=severity,
                        category="condition",
                        procedure_name=procedure_name,
                        detail=f"고객 질환 '{item_name}'이(가) 시술 금기사항에 해당합니다",
                        matched_customer_item=item_name,
                        matched_procedure_item=item_name,
                    )
                )

        # Check allergies
        contra_allergies = [
            a.lower() for a in contraindications.get("allergies", [])
        ]
        customer_allergies = self._extract_items(customer.allergies)
        for item_name in customer_allergies:
            if item_name.lower() in contra_allergies:
                warnings.append(
                    ContraindicationWarning(
                        severity="critical",
                        category="allergy",
                        procedure_name=procedure_name,
                        detail=f"고객 알레르기 '{item_name}'이(가) 시술 금기 알레르겐에 해당합니다",
                        matched_customer_item=item_name,
                        matched_procedure_item=item_name,
                    )
                )

        # Check medications
        contra_medications = [
            m.lower() for m in contraindications.get("medications", [])
        ]
        customer_medications = self._extract_items(customer.medications)
        for item_name in customer_medications:
            if item_name.lower() in contra_medications:
                warnings.append(
                    ContraindicationWarning(
                        severity="warning",
                        category="medication",
                        procedure_name=procedure_name,
                        detail=f"고객 복용약 '{item_name}'이(가) 시술 금기 약물에 해당합니다",
                        matched_customer_item=item_name,
                        matched_procedure_item=item_name,
                    )
                )

        critical_count = sum(1 for w in warnings if w.severity == "critical")
        warning_count = sum(1 for w in warnings if w.severity == "warning")
        info_count = sum(1 for w in warnings if w.severity == "info")

        return ContraindicationCheckResponse(
            has_warnings=len(warnings) > 0,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            warnings=warnings,
        )

    @staticmethod
    def _extract_items(health_data: dict | None) -> list[str]:
        """Extract item names from JSONB health data.

        Expected format: {"items": [{"name": "keloid", ...}]}
        """
        if not health_data:
            return []
        items = health_data.get("items", [])
        if not isinstance(items, list):
            return []
        return [item["name"] for item in items if isinstance(item, dict) and "name" in item]

    @staticmethod
    def _determine_severity(condition: str, dangerous_side_effects: str | None) -> str:
        if dangerous_side_effects and condition.lower() in dangerous_side_effects.lower():
            return "critical"
        return "warning"

    @staticmethod
    def _empty_response() -> ContraindicationCheckResponse:
        return ContraindicationCheckResponse(
            has_warnings=False,
            critical_count=0,
            warning_count=0,
            info_count=0,
            warnings=[],
        )
