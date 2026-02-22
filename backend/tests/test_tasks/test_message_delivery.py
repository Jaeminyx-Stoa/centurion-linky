"""Tests for message delivery retry task."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tasks.message_delivery import retry_message_delivery


@pytest.fixture
def mock_task():
    """Create a mock Celery task self object."""
    task = MagicMock()
    task.request.retries = 0
    task.max_retries = 5
    task.retry = MagicMock(side_effect=Exception("retry"))
    return task


class TestRetryMessageDelivery:
    @patch("app.tasks.message_delivery._deliver", new_callable=AsyncMock)
    def test_successful_delivery(self, mock_deliver):
        """Message delivery succeeds on first attempt."""
        mock_deliver.return_value = {
            "message_id": "msg-1",
            "messenger_message_id": "ext-123",
        }

        result = retry_message_delivery(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            "recipient-1",
            "Hello!",
            "telegram",
        )

        mock_deliver.assert_called_once()
        assert result["messenger_message_id"] == "ext-123"

    @patch("app.tasks.message_delivery._deliver", new_callable=AsyncMock)
    def test_delivery_failure_triggers_retry(self, mock_deliver, mock_task):
        """On failure, the task should call self.retry with exponential backoff."""
        mock_deliver.side_effect = ConnectionError("Connection refused")

        with pytest.raises(Exception, match="retry"):
            retry_message_delivery.__wrapped__(
                mock_task,
                str(uuid.uuid4()),
                str(uuid.uuid4()),
                "recipient-1",
                "Hello!",
                "telegram",
            )

        mock_task.retry.assert_called_once()
        call_kwargs = mock_task.retry.call_args
        assert call_kwargs.kwargs["countdown"] == 30  # 30 * 2^0

    @patch("app.tasks.message_delivery._notify_delivery_failed", new_callable=AsyncMock)
    @patch("app.tasks.message_delivery._deliver", new_callable=AsyncMock)
    def test_final_failure_sends_notification(
        self, mock_deliver, mock_notify, mock_task
    ):
        """After max retries, WebSocket delivery_failed notification is sent."""
        mock_deliver.side_effect = ConnectionError("Connection refused")
        mock_task.request.retries = 5  # Already at max
        mock_task.max_retries = 5
        mock_task.retry = MagicMock(side_effect=ConnectionError("final"))

        msg_id = str(uuid.uuid4())
        with pytest.raises(ConnectionError):
            retry_message_delivery.__wrapped__(
                mock_task,
                msg_id,
                str(uuid.uuid4()),
                "recipient-1",
                "Hello!",
                "telegram",
            )

        mock_notify.assert_called_once_with(msg_id, "telegram")

    @patch("app.tasks.message_delivery._deliver", new_callable=AsyncMock)
    def test_exponential_backoff_countdown(self, mock_deliver, mock_task):
        """Verify exponential backoff: 30, 60, 120, 240, 480."""
        mock_deliver.side_effect = ConnectionError("fail")

        for retry_num, expected_countdown in [(0, 30), (1, 60), (2, 120), (3, 240), (4, 480)]:
            mock_task.request.retries = retry_num
            mock_task.retry.reset_mock()
            mock_task.retry.side_effect = Exception("retry")

            with pytest.raises(Exception, match="retry"):
                retry_message_delivery.__wrapped__(
                    mock_task,
                    str(uuid.uuid4()),
                    str(uuid.uuid4()),
                    "recipient-1",
                    "Hello!",
                    "telegram",
                )

            actual_countdown = mock_task.retry.call_args.kwargs["countdown"]
            assert actual_countdown == expected_countdown, (
                f"Retry {retry_num}: expected {expected_countdown}, got {actual_countdown}"
            )
