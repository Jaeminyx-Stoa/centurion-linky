"""Celery app configuration and task definitions."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "medical_messenger",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="Asia/Seoul",
    enable_utc=True,

    # Reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Retry defaults
    task_default_retry_delay=10,
    task_max_retries=3,

    # Result expiration (24h)
    result_expires=86400,

    # Task time limits
    task_soft_time_limit=120,  # 2 min soft limit
    task_time_limit=180,  # 3 min hard limit

    # Task routing
    task_routes={
        "app.tasks.ai_response.*": {"queue": "ai"},
        "app.tasks.crm_execution.*": {"queue": "default"},
        "app.tasks.message_delivery.*": {"queue": "default"},
        "app.tasks.notifications.*": {"queue": "default"},
    },

    # Dead letter
    task_reject_on_worker_lost=True,

    # Broker connection resilience
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,
    broker_pool_limit=10,

    # Celery Beat schedule
    beat_schedule={
        "execute-due-crm-events": {
            "task": "app.tasks.crm_execution.execute_due_events",
            "schedule": 300.0,  # every 5 minutes
        },
        "reindex-pending-embeddings": {
            "task": "app.tasks.indexing.reindex_pending",
            "schedule": 1800.0,  # every 30 minutes
        },
        "monthly-performance": {
            "task": "app.tasks.analytics.calculate_monthly_performance",
            "schedule": crontab(day_of_month=1, hour=2, minute=0),
        },
        "monthly-settlements": {
            "task": "app.tasks.analytics.generate_monthly_settlements",
            "schedule": crontab(day_of_month=1, hour=3, minute=0),
        },
        "summarize-conversations": {
            "task": "app.tasks.analytics.summarize_conversations",
            "schedule": crontab(minute=0),  # every hour
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
