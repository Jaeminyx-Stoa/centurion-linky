"""Resilience utilities: Circuit Breaker, retry, and HTTP client factory.

Provides:
- CircuitBreaker: lightweight async circuit breaker (CLOSED -> OPEN -> HALF_OPEN)
- retry_async: tenacity-based decorator factory with exponential backoff
- get_http_client: httpx.AsyncClient factory with configured timeout
"""

import logging
import time
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""

    def __init__(self, name: str):
        super().__init__(f"Circuit breaker '{name}' is OPEN")
        self.name = name


class CircuitBreaker:
    """Lightweight async circuit breaker.

    - CLOSED: calls pass through; failures are counted.
    - OPEN: calls are rejected immediately with CircuitBreakerOpenError.
    - HALF_OPEN: a single probe call is allowed; success resets to CLOSED,
      failure re-opens.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int | None = None,
        recovery_timeout: int | None = None,
    ):
        self.name = name
        self.failure_threshold = (
            failure_threshold or settings.circuit_breaker_failure_threshold
        )
        self.recovery_timeout = (
            recovery_timeout or settings.circuit_breaker_recovery_timeout
        )
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0

    async def call(
        self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute *func* through the circuit breaker."""
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit '%s' entering HALF_OPEN", self.name)
            else:
                raise CircuitBreakerOpenError(self.name)

        try:
            result = await func(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def _record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit '%s' OPEN after %d failures",
                self.name,
                self._failure_count,
            )

    def _record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit '%s' recovered -> CLOSED", self.name)
        self._failure_count = 0
        self.state = CircuitState.CLOSED


def retry_async(
    max_retries: int | None = None,
    retry_on: tuple[type[Exception], ...] = (
        httpx.ConnectError,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
    ),
):
    """Tenacity-based retry decorator factory with exponential backoff."""
    attempts = max_retries if max_retries is not None else settings.http_max_retries
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
        retry=retry_if_exception_type(retry_on),
        reraise=True,
    )


def get_http_client(**kwargs: Any) -> httpx.AsyncClient:
    """Return an httpx.AsyncClient with configured timeout."""
    timeout = httpx.Timeout(settings.http_timeout_seconds)
    return httpx.AsyncClient(timeout=timeout, **kwargs)
