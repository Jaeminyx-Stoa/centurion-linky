"""Tests for protocol-related agent tools."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestProtocolTools:
    @pytest.mark.asyncio
    async def test_tools_include_protocol_tools(self):
        """Verify that create_consultation_tools includes protocol tools."""
        from app.ai.agents.tools import create_consultation_tools

        db = AsyncMock()
        tools = create_consultation_tools(
            db=db,
            clinic_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
        )

        tool_names = [t.name for t in tools]
        assert "get_protocol_checklist" in tool_names
        assert "update_protocol_item" in tool_names
        assert "check_contraindications" in tool_names

    @pytest.mark.asyncio
    async def test_tools_count(self):
        """Verify total tool count."""
        from app.ai.agents.tools import create_consultation_tools

        db = AsyncMock()
        tools = create_consultation_tools(
            db=db,
            clinic_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
        )
        # search_procedures, create_booking, send_payment_link,
        # check_availability, escalate_to_human, get_clinic_info,
        # check_contraindications, get_protocol_checklist, update_protocol_item
        assert len(tools) == 9
