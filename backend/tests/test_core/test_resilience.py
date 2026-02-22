"""Tests for app.core.resilience: CircuitBreaker, retry_async, get_http_client."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    get_http_client,
    retry_async,
)


# ──────────────────────────────────────────────
# CircuitBreaker
# ──────────────────────────────────────────────
class TestCircuitBreaker:
    @pytest.fixture
    def cb(self):
        return CircuitBreaker("test", failure_threshold=3, recovery_timeout=1)

    async def test_starts_closed(self, cb):
        assert cb.state == CircuitState.CLOSED

    async def test_success_stays_closed(self, cb):
        func = AsyncMock(return_value="ok")
        result = await cb.call(func)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    async def test_opens_after_threshold_failures(self, cb):
        func = AsyncMock(side_effect=RuntimeError("fail"))

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(func)

        assert cb.state == CircuitState.OPEN

    async def test_open_rejects_immediately(self, cb):
        func = AsyncMock(side_effect=RuntimeError("fail"))

        # Trip the breaker
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(func)

        # Next call should get CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(func)

    async def test_half_open_after_recovery_timeout(self, cb):
        func_fail = AsyncMock(side_effect=RuntimeError("fail"))

        # Trip
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(func_fail)

        assert cb.state == CircuitState.OPEN

        # Simulate elapsed time
        cb._last_failure_time = time.monotonic() - 2  # past recovery_timeout=1

        # Next call should be allowed (HALF_OPEN)
        func_ok = AsyncMock(return_value="recovered")
        result = await cb.call(func_ok)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    async def test_half_open_failure_reopens(self, cb):
        func_fail = AsyncMock(side_effect=RuntimeError("fail"))

        # Trip
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(func_fail)

        # Simulate elapsed time
        cb._last_failure_time = time.monotonic() - 2

        # Probe fails -> back to OPEN
        with pytest.raises(RuntimeError):
            await cb.call(func_fail)

        assert cb.state == CircuitState.OPEN


# ──────────────────────────────────────────────
# retry_async
# ──────────────────────────────────────────────
class TestRetryAsync:
    async def test_retries_on_transient_error_then_succeeds(self):
        call_count = 0

        @retry_async(max_retries=3, retry_on=(httpx.ConnectError,))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("connection refused")
            return "success"

        result = await flaky()
        assert result == "success"
        assert call_count == 3

    async def test_raises_after_max_retries(self):
        @retry_async(max_retries=2, retry_on=(httpx.ConnectError,))
        async def always_fail():
            raise httpx.ConnectError("connection refused")

        with pytest.raises(httpx.ConnectError):
            await always_fail()

    async def test_non_retryable_error_propagates_immediately(self):
        call_count = 0

        @retry_async(max_retries=3, retry_on=(httpx.ConnectError,))
        async def value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            await value_error()

        assert call_count == 1


# ──────────────────────────────────────────────
# get_http_client
# ──────────────────────────────────────────────
class TestGetHttpClient:
    async def test_returns_async_client_with_timeout(self):
        client = get_http_client()
        assert isinstance(client, httpx.AsyncClient)
        assert client.timeout.connect is not None
        await client.aclose()

    @patch("app.core.resilience.settings")
    async def test_uses_configured_timeout(self, mock_settings):
        mock_settings.http_timeout_seconds = 15
        client = get_http_client()
        assert client.timeout.connect == 15
        assert client.timeout.read == 15
        await client.aclose()
