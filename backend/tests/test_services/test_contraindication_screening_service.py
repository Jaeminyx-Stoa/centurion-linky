"""Tests for ContraindicationScreeningService (auto-screening in AI chat)."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.contraindication_screening_service import (
    ContraindicationScreeningService,
)


@pytest.fixture
def clinic_id():
    return uuid.uuid4()


@pytest.fixture
def conversation_id():
    return uuid.uuid4()


@pytest.fixture
def customer_id():
    return uuid.uuid4()


def _make_conversation(conversation_id, clinic_id, customer_id):
    conv = MagicMock()
    conv.id = conversation_id
    conv.clinic_id = clinic_id
    conv.customer_id = customer_id
    return conv


def _make_customer(customer_id, clinic_id, conditions=None, allergies=None, medications=None):
    customer = MagicMock()
    customer.id = customer_id
    customer.clinic_id = clinic_id
    customer.name = "홍길동"
    customer.display_name = "홍길동"
    customer.medical_conditions = conditions
    customer.allergies = allergies
    customer.medications = medications
    return customer


class TestContraindicationScreening:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_health_mentions(self, clinic_id, conversation_id):
        """No health data extracted → returns None."""
        db = AsyncMock()
        svc = ContraindicationScreeningService(db)

        llm_response = MagicMock()
        llm_response.content = json.dumps({
            "conditions": [],
            "allergies": [],
            "medications": [],
            "mentioned_procedures": [],
        })

        with patch(
            "app.services.contraindication_screening_service.get_light_llm"
        ) as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=llm_response)
            result = await svc.screen_message(
                "안녕하세요, 상담 예약하고 싶어요",
                conversation_id,
                clinic_id,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_extracts_and_returns_alert_with_warnings(
        self, clinic_id, conversation_id, customer_id
    ):
        """Health data extracted + contraindication match → returns alert."""
        conv = _make_conversation(conversation_id, clinic_id, customer_id)
        customer = _make_customer(
            customer_id,
            clinic_id,
            conditions={"items": []},
            allergies={"items": []},
        )

        db = AsyncMock()
        # Conversation lookup
        conv_result = MagicMock(scalar_one_or_none=MagicMock(return_value=conv))
        # Customer lookup
        cust_result = MagicMock(scalar_one_or_none=MagicMock(return_value=customer))
        # No mentioned procedures → booking query returns empty
        booking_result = MagicMock()
        booking_result.all.return_value = []
        db.execute = AsyncMock(side_effect=[conv_result, cust_result, booking_result])
        db.flush = AsyncMock()

        llm_response = MagicMock()
        llm_response.content = json.dumps({
            "conditions": ["pregnancy"],
            "allergies": [],
            "medications": [],
            "mentioned_procedures": [],
        })

        with patch(
            "app.services.contraindication_screening_service.get_light_llm"
        ) as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=llm_response)
            result = await svc.screen_message(
                "임신 중인데 보톡스 가능한가요?",
                conversation_id,
                clinic_id,
            )

        # Customer health data should be updated
        assert customer.medical_conditions is not None
        items = customer.medical_conditions.get("items", [])
        assert any(i["name"] == "pregnancy" for i in items)

    @pytest.mark.asyncio
    async def test_returns_none_when_conversation_not_found(
        self, clinic_id, conversation_id
    ):
        """Conversation not found → returns None."""
        db = AsyncMock()
        conv_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        db.execute = AsyncMock(return_value=conv_result)

        svc = ContraindicationScreeningService(db)

        llm_response = MagicMock()
        llm_response.content = json.dumps({
            "conditions": ["keloid"],
            "allergies": [],
            "medications": [],
            "mentioned_procedures": [],
        })

        with patch(
            "app.services.contraindication_screening_service.get_light_llm"
        ) as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=llm_response)
            result = await svc.screen_message(
                "켈로이드 체질인데요",
                conversation_id,
                clinic_id,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_llm_json_error(self, clinic_id, conversation_id):
        """LLM returns non-JSON → returns None."""
        db = AsyncMock()
        svc = ContraindicationScreeningService(db)

        llm_response = MagicMock()
        llm_response.content = "Sorry, I can't process that."

        with patch(
            "app.services.contraindication_screening_service.get_light_llm"
        ) as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=llm_response)
            result = await svc.screen_message(
                "some message",
                conversation_id,
                clinic_id,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_merges_health_data_without_duplicates(
        self, clinic_id, conversation_id, customer_id
    ):
        """Existing health items should not be duplicated."""
        conv = _make_conversation(conversation_id, clinic_id, customer_id)
        customer = _make_customer(
            customer_id,
            clinic_id,
            conditions={"items": [{"name": "diabetes", "source": "manual"}]},
            allergies={"items": []},
        )

        db = AsyncMock()
        conv_result = MagicMock(scalar_one_or_none=MagicMock(return_value=conv))
        cust_result = MagicMock(scalar_one_or_none=MagicMock(return_value=customer))
        booking_result = MagicMock()
        booking_result.all.return_value = []
        db.execute = AsyncMock(side_effect=[conv_result, cust_result, booking_result])
        db.flush = AsyncMock()

        llm_response = MagicMock()
        llm_response.content = json.dumps({
            "conditions": ["diabetes", "hypertension"],
            "allergies": [],
            "medications": [],
            "mentioned_procedures": [],
        })

        svc = ContraindicationScreeningService(db)

        with patch(
            "app.services.contraindication_screening_service.get_light_llm"
        ) as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=llm_response)
            await svc.screen_message(
                "당뇨와 고혈압이 있어요",
                conversation_id,
                clinic_id,
            )

        items = customer.medical_conditions["items"]
        names = [i["name"] for i in items]
        # diabetes should appear only once (existing), hypertension added
        assert names.count("diabetes") == 1
        assert "hypertension" in names
        assert len(items) == 2
