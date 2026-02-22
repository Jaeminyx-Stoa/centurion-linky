"""Tests for LLM quota checking in UsageTracker."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.ai.usage_tracker import UsageTracker


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def clinic_id():
    return uuid.uuid4()


@pytest.fixture
def tracker(mock_db, clinic_id):
    return UsageTracker(mock_db, clinic_id)


class TestQuotaCheck:
    @pytest.mark.asyncio
    async def test_no_alert_when_quota_not_set(self, tracker, mock_db):
        """No alert should be sent if clinic has no quota configured."""
        mock_clinic = MagicMock()
        mock_clinic.llm_monthly_quota_usd = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_clinic
        mock_db.execute.return_value = mock_result

        with patch("app.ai.usage_tracker.manager") as mock_manager:
            await tracker._check_quota()
            mock_manager.broadcast_to_clinic.assert_not_called()

    @pytest.mark.asyncio
    async def test_warning_at_80_percent(self, tracker, mock_db, clinic_id):
        """Should send quota_warning when usage reaches 80%."""
        mock_clinic = MagicMock()
        mock_clinic.llm_monthly_quota_usd = 100.0
        mock_clinic.llm_quota_alert_sent = False

        # First execute returns clinic, second returns cost
        clinic_result = MagicMock()
        clinic_result.scalar_one_or_none.return_value = mock_clinic

        cost_result = MagicMock()
        cost_result.scalar.return_value = 85.0  # 85% usage

        mock_db.execute.side_effect = [clinic_result, cost_result]

        with patch("app.ai.usage_tracker.manager") as mock_manager:
            mock_manager.broadcast_to_clinic = AsyncMock()
            await tracker._check_quota()

            mock_manager.broadcast_to_clinic.assert_called_once()
            call_args = mock_manager.broadcast_to_clinic.call_args
            assert call_args[0][0] == clinic_id
            assert call_args[0][1]["type"] == "quota_warning"
            assert mock_clinic.llm_quota_alert_sent is True

    @pytest.mark.asyncio
    async def test_exceeded_at_100_percent(self, tracker, mock_db, clinic_id):
        """Should send quota_exceeded when usage reaches 100%."""
        mock_clinic = MagicMock()
        mock_clinic.llm_monthly_quota_usd = 50.0
        mock_clinic.llm_quota_alert_sent = False

        clinic_result = MagicMock()
        clinic_result.scalar_one_or_none.return_value = mock_clinic

        cost_result = MagicMock()
        cost_result.scalar.return_value = 55.0  # 110% usage

        mock_db.execute.side_effect = [clinic_result, cost_result]

        with patch("app.ai.usage_tracker.manager") as mock_manager:
            mock_manager.broadcast_to_clinic = AsyncMock()
            await tracker._check_quota()

            call_args = mock_manager.broadcast_to_clinic.call_args
            assert call_args[0][1]["type"] == "quota_exceeded"
            assert mock_clinic.llm_quota_alert_sent is True

    @pytest.mark.asyncio
    async def test_no_duplicate_alert(self, tracker, mock_db):
        """Should not send alert if llm_quota_alert_sent is already True."""
        mock_clinic = MagicMock()
        mock_clinic.llm_monthly_quota_usd = 100.0
        mock_clinic.llm_quota_alert_sent = True  # Already sent

        clinic_result = MagicMock()
        clinic_result.scalar_one_or_none.return_value = mock_clinic

        cost_result = MagicMock()
        cost_result.scalar.return_value = 95.0

        mock_db.execute.side_effect = [clinic_result, cost_result]

        with patch("app.ai.usage_tracker.manager") as mock_manager:
            mock_manager.broadcast_to_clinic = AsyncMock()
            await tracker._check_quota()

            mock_manager.broadcast_to_clinic.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_alert_below_80_percent(self, tracker, mock_db):
        """No alert when usage is below 80%."""
        mock_clinic = MagicMock()
        mock_clinic.llm_monthly_quota_usd = 100.0
        mock_clinic.llm_quota_alert_sent = False

        clinic_result = MagicMock()
        clinic_result.scalar_one_or_none.return_value = mock_clinic

        cost_result = MagicMock()
        cost_result.scalar.return_value = 50.0  # 50% usage

        mock_db.execute.side_effect = [clinic_result, cost_result]

        with patch("app.ai.usage_tracker.manager") as mock_manager:
            mock_manager.broadcast_to_clinic = AsyncMock()
            await tracker._check_quota()

            mock_manager.broadcast_to_clinic.assert_not_called()
            assert mock_clinic.llm_quota_alert_sent is False
