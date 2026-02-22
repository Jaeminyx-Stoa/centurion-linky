"""Tests for LLM usage tracker, cost calculation, and tracked_ainvoke."""

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.tracked_llm import tracked_ainvoke
from app.ai.usage_tracker import UsageTracker, calculate_cost


class TestCalculateCost:
    def test_known_model_claude(self):
        cost = calculate_cost("claude-3-5-sonnet-20241022", 1000, 500)
        # 1000 * 0.003/1000 + 500 * 0.015/1000 = 0.003 + 0.0075 = 0.0105
        assert abs(cost - 0.0105) < 1e-8

    def test_known_model_gpt4o_mini(self):
        cost = calculate_cost("gpt-4o-mini", 2000, 1000)
        # 2000 * 0.00015/1000 + 1000 * 0.0006/1000 = 0.0003 + 0.0006 = 0.0009
        assert abs(cost - 0.0009) < 1e-8

    def test_known_model_gemini_flash(self):
        cost = calculate_cost("gemini-1.5-flash-latest", 10000, 5000)
        # 10000 * 0.000075/1000 + 5000 * 0.0003/1000 = 0.00075 + 0.0015 = 0.00225
        assert abs(cost - 0.00225) < 1e-8

    def test_unknown_model_uses_default(self):
        cost = calculate_cost("totally-unknown-model", 1000, 1000)
        # 1000 * 0.002/1000 + 1000 * 0.008/1000 = 0.002 + 0.008 = 0.01
        assert abs(cost - 0.01) < 1e-8

    def test_zero_tokens(self):
        cost = calculate_cost("gpt-4o", 0, 0)
        assert cost == 0.0


class TestUsageTracker:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def tracker(self, mock_db):
        return UsageTracker(
            db=mock_db,
            clinic_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            message_id=uuid.uuid4(),
        )

    def test_record_buffers_usage(self, tracker):
        tracker.record(
            provider="anthropic",
            model_name="claude-3-5-sonnet",
            operation="consultation",
            input_tokens=100,
            output_tokens=50,
            latency_ms=500,
        )
        assert len(tracker._records) == 1
        rec = tracker._records[0]
        assert rec.total_tokens == 150
        assert rec.cost_usd > 0
        assert rec.success is True

    def test_record_failure(self, tracker):
        tracker.record(
            provider="anthropic",
            model_name="claude-3-5-sonnet",
            operation="consultation",
            success=False,
            error_message="API error",
        )
        assert len(tracker._records) == 1
        assert tracker._records[0].success is False
        assert tracker._records[0].error_message == "API error"

    async def test_flush_writes_to_db(self, tracker, mock_db):
        tracker.record(
            provider="anthropic",
            model_name="claude-3-5-sonnet",
            operation="satisfaction",
            input_tokens=50,
            output_tokens=20,
        )
        tracker.record(
            provider="google",
            model_name="gemini-1.5-flash",
            operation="summarization",
            input_tokens=200,
            output_tokens=100,
        )

        await tracker.flush()

        assert mock_db.add.call_count == 2
        assert len(tracker._records) == 0

    async def test_flush_empty_does_nothing(self, tracker, mock_db):
        await tracker.flush()
        mock_db.add.assert_not_called()


class TestTrackedAinvoke:
    @pytest.fixture
    def mock_tracker(self):
        return MagicMock(spec=UsageTracker)

    async def test_success_records_usage(self, mock_tracker):
        @dataclass
        class FakeResult:
            content: str = "Hello"
            usage_metadata: dict = None
            response_metadata: dict = None

            def __post_init__(self):
                self.usage_metadata = {"input_tokens": 100, "output_tokens": 50}
                self.response_metadata = {"model_name": "claude-3-5-sonnet-20241022"}

        llm = AsyncMock()
        llm.ainvoke.return_value = FakeResult()
        llm.model_name = "claude-3-5-sonnet"

        result = await tracked_ainvoke(
            llm, "test prompt", tracker=mock_tracker, operation="consultation"
        )

        assert result.content == "Hello"
        mock_tracker.record.assert_called_once()
        call_kwargs = mock_tracker.record.call_args.kwargs
        assert call_kwargs["operation"] == "consultation"
        assert call_kwargs["input_tokens"] == 100
        assert call_kwargs["output_tokens"] == 50
        assert call_kwargs["success"] is True

    async def test_failure_records_error_and_reraises(self, mock_tracker):
        llm = AsyncMock()
        llm.ainvoke.side_effect = RuntimeError("LLM failed")
        llm.model_name = "gpt-4o"

        with pytest.raises(RuntimeError, match="LLM failed"):
            await tracked_ainvoke(
                llm, "test prompt", tracker=mock_tracker, operation="satisfaction"
            )

        mock_tracker.record.assert_called_once()
        call_kwargs = mock_tracker.record.call_args.kwargs
        assert call_kwargs["success"] is False
        assert "LLM failed" in call_kwargs["error_message"]
