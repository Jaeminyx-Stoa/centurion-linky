"""Tests for ContraindicationService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.contraindication import ContraindicationCheckResponse
from app.services.contraindication_service import ContraindicationService


@pytest.fixture
def clinic_id():
    return uuid.uuid4()


@pytest.fixture
def customer_id():
    return uuid.uuid4()


@pytest.fixture
def cp_id():
    return uuid.uuid4()


def _make_customer(
    customer_id, clinic_id, conditions=None, allergies=None, medications=None
):
    customer = MagicMock()
    customer.id = customer_id
    customer.clinic_id = clinic_id
    customer.medical_conditions = conditions
    customer.allergies = allergies
    customer.medications = medications
    return customer


def _make_procedure(contraindications=None, dangerous_side_effects=None):
    proc = MagicMock()
    proc.name_ko = "보톡스"
    proc.contraindications = contraindications
    proc.dangerous_side_effects = dangerous_side_effects
    return proc


def _make_clinic_procedure(cp_id, clinic_id, procedure_id):
    cp = MagicMock()
    cp.id = cp_id
    cp.clinic_id = clinic_id
    cp.procedure_id = procedure_id
    return cp


class TestContraindicationService:
    @pytest.mark.asyncio
    async def test_no_warnings_when_no_health_data(
        self, clinic_id, customer_id, cp_id
    ):
        proc_id = uuid.uuid4()
        customer = _make_customer(customer_id, clinic_id)
        cp = _make_clinic_procedure(cp_id, clinic_id, proc_id)
        procedure = _make_procedure(
            contraindications={"conditions": ["keloid"], "allergies": [], "medications": []}
        )

        db = AsyncMock()
        # customer query
        db.execute = AsyncMock()
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=customer)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=cp)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=procedure)),
        ]
        db.execute.side_effect = results

        svc = ContraindicationService(db)
        result = await svc.check(customer_id, cp_id, clinic_id)

        assert isinstance(result, ContraindicationCheckResponse)
        assert result.has_warnings is False
        assert result.critical_count == 0

    @pytest.mark.asyncio
    async def test_condition_match_produces_warning(
        self, clinic_id, customer_id, cp_id
    ):
        proc_id = uuid.uuid4()
        customer = _make_customer(
            customer_id,
            clinic_id,
            conditions={"items": [{"name": "keloid", "severity": "moderate"}]},
        )
        cp = _make_clinic_procedure(cp_id, clinic_id, proc_id)
        procedure = _make_procedure(
            contraindications={"conditions": ["keloid"], "allergies": [], "medications": []}
        )

        db = AsyncMock()
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=customer)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=cp)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=procedure)),
        ]
        db.execute.side_effect = results

        svc = ContraindicationService(db)
        result = await svc.check(customer_id, cp_id, clinic_id)

        assert result.has_warnings is True
        assert len(result.warnings) == 1
        assert result.warnings[0].category == "condition"
        assert result.warnings[0].matched_customer_item == "keloid"

    @pytest.mark.asyncio
    async def test_allergy_match_is_critical(
        self, clinic_id, customer_id, cp_id
    ):
        proc_id = uuid.uuid4()
        customer = _make_customer(
            customer_id,
            clinic_id,
            allergies={"items": [{"name": "lidocaine"}]},
        )
        cp = _make_clinic_procedure(cp_id, clinic_id, proc_id)
        procedure = _make_procedure(
            contraindications={"conditions": [], "allergies": ["lidocaine"], "medications": []}
        )

        db = AsyncMock()
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=customer)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=cp)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=procedure)),
        ]
        db.execute.side_effect = results

        svc = ContraindicationService(db)
        result = await svc.check(customer_id, cp_id, clinic_id)

        assert result.has_warnings is True
        assert result.critical_count == 1
        assert result.warnings[0].severity == "critical"
        assert result.warnings[0].category == "allergy"

    @pytest.mark.asyncio
    async def test_medication_match_is_warning(
        self, clinic_id, customer_id, cp_id
    ):
        proc_id = uuid.uuid4()
        customer = _make_customer(
            customer_id,
            clinic_id,
            medications={"items": [{"name": "blood_thinners"}]},
        )
        cp = _make_clinic_procedure(cp_id, clinic_id, proc_id)
        procedure = _make_procedure(
            contraindications={"conditions": [], "allergies": [], "medications": ["blood_thinners"]}
        )

        db = AsyncMock()
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=customer)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=cp)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=procedure)),
        ]
        db.execute.side_effect = results

        svc = ContraindicationService(db)
        result = await svc.check(customer_id, cp_id, clinic_id)

        assert result.has_warnings is True
        assert result.warning_count == 1
        assert result.warnings[0].severity == "warning"
        assert result.warnings[0].category == "medication"

    @pytest.mark.asyncio
    async def test_empty_contraindications_no_warnings(
        self, clinic_id, customer_id, cp_id
    ):
        proc_id = uuid.uuid4()
        customer = _make_customer(
            customer_id,
            clinic_id,
            conditions={"items": [{"name": "keloid"}]},
        )
        cp = _make_clinic_procedure(cp_id, clinic_id, proc_id)
        procedure = _make_procedure(contraindications={})

        db = AsyncMock()
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=customer)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=cp)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=procedure)),
        ]
        db.execute.side_effect = results

        svc = ContraindicationService(db)
        result = await svc.check(customer_id, cp_id, clinic_id)

        assert result.has_warnings is False

    @pytest.mark.asyncio
    async def test_customer_not_found_returns_empty(
        self, clinic_id, customer_id, cp_id
    ):
        db = AsyncMock()
        db.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        svc = ContraindicationService(db)
        result = await svc.check(customer_id, cp_id, clinic_id)

        assert result.has_warnings is False
        assert result.warnings == []

    def test_extract_items_with_none(self):
        assert ContraindicationService._extract_items(None) == []

    def test_extract_items_with_valid_data(self):
        data = {"items": [{"name": "keloid"}, {"name": "pregnancy"}]}
        assert ContraindicationService._extract_items(data) == ["keloid", "pregnancy"]

    def test_extract_items_with_empty_items(self):
        assert ContraindicationService._extract_items({"items": []}) == []

    def test_extract_items_with_malformed_data(self):
        assert ContraindicationService._extract_items({"items": "invalid"}) == []
