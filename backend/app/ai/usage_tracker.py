"""LLM usage tracker — records token counts and costs per invocation."""

import logging
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_usage import LLMUsage

logger = logging.getLogger(__name__)

# Cost per 1K tokens (USD) — input / output
COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    # Anthropic
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku": {"input": 0.001, "output": 0.005},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4": {"input": 0.003, "output": 0.015},
    "claude-haiku-4": {"input": 0.001, "output": 0.005},
    # Azure OpenAI
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    # Google
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
}

# Fallback for unknown models
_DEFAULT_COST = {"input": 0.002, "output": 0.008}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost from model name and token counts."""
    # Match by prefix (e.g. "claude-3-5-sonnet-20241022" -> "claude-3-5-sonnet")
    costs = _DEFAULT_COST
    for key, val in COST_PER_1K_TOKENS.items():
        if key in model_name.lower():
            costs = val
            break

    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000


class UsageTracker:
    """Accumulates LLM usage records and flushes them to the database."""

    def __init__(
        self,
        db: AsyncSession,
        clinic_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
    ):
        self._db = db
        self._clinic_id = clinic_id
        self._conversation_id = conversation_id
        self._message_id = message_id
        self._records: list[LLMUsage] = []

    def record(
        self,
        *,
        provider: str,
        model_name: str,
        operation: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> None:
        """Buffer a single usage record."""
        total_tokens = input_tokens + output_tokens
        cost = calculate_cost(model_name, input_tokens, output_tokens)

        self._records.append(
            LLMUsage(
                id=uuid.uuid4(),
                clinic_id=self._clinic_id,
                conversation_id=self._conversation_id,
                message_id=self._message_id,
                provider=provider,
                model_name=model_name,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
            )
        )

    async def flush(self) -> None:
        """Write all buffered records to the database and check quota."""
        if not self._records:
            return
        for record in self._records:
            self._db.add(record)
        logger.info(
            "Flushing %d LLM usage records (clinic=%s)",
            len(self._records),
            self._clinic_id,
        )
        self._records.clear()

        # Check quota after flushing
        await self._check_quota()

    async def _check_quota(self) -> None:
        """Check monthly LLM cost against clinic quota and send alerts."""
        from app.models.clinic import Clinic

        result = await self._db.execute(
            select(Clinic).where(Clinic.id == self._clinic_id)
        )
        clinic = result.scalar_one_or_none()
        if clinic is None or clinic.llm_monthly_quota_usd is None:
            return

        # Calculate current month's total cost
        today = date.today()
        start_of_month = date(today.year, today.month, 1)

        cost_result = await self._db.execute(
            select(func.coalesce(func.sum(LLMUsage.cost_usd), 0.0)).where(
                LLMUsage.clinic_id == self._clinic_id,
                func.date(LLMUsage.created_at) >= start_of_month,
            )
        )
        monthly_cost = float(cost_result.scalar() or 0.0)

        quota = clinic.llm_monthly_quota_usd
        ratio = monthly_cost / quota if quota > 0 else 0

        if ratio >= 1.0 and not clinic.llm_quota_alert_sent:
            # 100% — exceeded
            clinic.llm_quota_alert_sent = True
            await self._send_quota_alert("quota_exceeded", monthly_cost, quota)
        elif ratio >= 0.8 and not clinic.llm_quota_alert_sent:
            # 80% — warning
            clinic.llm_quota_alert_sent = True
            await self._send_quota_alert("quota_warning", monthly_cost, quota)

    async def _send_quota_alert(
        self, alert_type: str, current_cost: float, quota: float
    ) -> None:
        """Broadcast a quota alert via WebSocket."""
        from app.websocket.manager import manager

        await manager.broadcast_to_clinic(
            self._clinic_id,
            {
                "type": alert_type,
                "current_cost_usd": round(current_cost, 4),
                "quota_usd": round(quota, 2),
                "usage_percent": round(current_cost / quota * 100, 1) if quota > 0 else 0,
            },
        )
