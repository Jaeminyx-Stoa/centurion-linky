"""Prometheus metrics middleware using prometheus-fastapi-instrumentator."""

from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Custom metrics
WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Number of active WebSocket connections",
    ["clinic_id"],
)

CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_dispatched_total",
    "Total Celery tasks dispatched from web process",
    ["task_name"],
)

AI_RESPONSE_DURATION = Histogram(
    "ai_response_duration_seconds",
    "Time spent generating AI responses",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)


def setup_metrics(app):
    """Attach Prometheus metrics to the FastAPI app.

    Exposes /metrics endpoint with:
    - HTTP request count, latency, and size (auto-instrumented)
    - Custom WebSocket, Celery, and AI metrics
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics"],
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
