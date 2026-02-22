"""Tracked LLM invocation — wraps ainvoke to capture usage metadata."""

import logging
import time
from typing import Any

from app.ai.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


async def tracked_ainvoke(
    llm: Any,
    prompt: str | Any,
    *,
    tracker: UsageTracker,
    operation: str,
) -> Any:
    """Invoke an LLM and record token/cost data via the tracker.

    Extracts usage_metadata and response_metadata from the LangChain result.
    On failure, records the error and re-raises.
    """
    start = time.monotonic()
    try:
        result = await llm.ainvoke(prompt)
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        model_name = getattr(llm, "model_name", None) or getattr(llm, "model", "unknown")
        provider = _detect_provider(model_name)
        tracker.record(
            provider=provider,
            model_name=str(model_name),
            operation=operation,
            latency_ms=elapsed_ms,
            success=False,
            error_message=str(exc)[:500],
        )
        raise

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Extract token usage from LangChain result
    usage = getattr(result, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
    output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0

    # Extract model name from response metadata (actual model used)
    resp_meta = getattr(result, "response_metadata", None) or {}
    actual_model = (
        resp_meta.get("model_name")
        or resp_meta.get("model")
        or getattr(llm, "model_name", None)
        or getattr(llm, "model", "unknown")
    )

    provider = _detect_provider(str(actual_model))

    tracker.record(
        provider=provider,
        model_name=str(actual_model),
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=elapsed_ms,
        success=True,
    )

    return result


def _detect_provider(model_name: str) -> str:
    """Guess provider from model name string."""
    name = model_name.lower()
    if "claude" in name:
        return "anthropic"
    if "gpt" in name:
        return "azure_openai"
    if "gemini" in name:
        return "google"
    return "unknown"
