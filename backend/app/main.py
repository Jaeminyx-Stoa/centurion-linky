import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import router as v1_router
from app.api.webhooks.kakao import router as kakao_webhook_router
from app.api.webhooks.line import router as line_webhook_router
from app.api.webhooks.meta import router as meta_webhook_router
from app.api.webhooks.payments import router as payment_webhook_router
from app.api.webhooks.telegram import router as telegram_webhook_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.logging import setup_logging
from app.middleware.body_limit import BodyLimitMiddleware
from app.middleware.metrics import setup_metrics
from app.middleware.rate_limit import limiter
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.websocket.endpoint import router as ws_router

# Static file serving for local dev uploads
import os

if os.path.exists("uploads") or settings.app_env == "development":
    from fastapi.staticfiles import StaticFiles

    os.makedirs("uploads", exist_ok=True)
from app.websocket.manager import manager as ws_manager

logger = logging.getLogger(__name__)

setup_logging(settings.app_env, settings.app_debug)

app = FastAPI(
    title="Medical Messenger MVP",
    version="0.1.0",
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware order: outermost first
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodyLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Accept-Language", "X-Request-ID"],
)

# Prometheus metrics
setup_metrics(app)

app.include_router(v1_router)
app.include_router(telegram_webhook_router, prefix="/api")
app.include_router(meta_webhook_router, prefix="/api")
app.include_router(line_webhook_router, prefix="/api")
app.include_router(kakao_webhook_router, prefix="/api")
app.include_router(payment_webhook_router, prefix="/api")
app.include_router(ws_router)

# Serve local uploads in development
if os.path.exists("uploads"):
    app.mount("/static/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup_event():
    await ws_manager.start_listener()


@app.on_event("shutdown")
async def shutdown_event():
    await ws_manager.stop_listener()

    # Drain DB connection pool
    from app.core.database import engine

    await engine.dispose()
    logger.info("Application shutdown complete")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health_check():
    import asyncio

    checks: dict[str, str] = {}
    status = "ok"

    # DB check
    try:
        from app.core.database import engine

        async with asyncio.timeout(5):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
        status = "degraded"

    # Redis check
    try:
        import redis.asyncio as aioredis

        async with asyncio.timeout(5):
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.aclose()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
        status = "degraded"

    # RabbitMQ check (TCP connect to broker)
    try:
        from urllib.parse import urlparse

        async with asyncio.timeout(5):
            parsed = urlparse(settings.rabbitmq_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 5672
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
        checks["rabbitmq"] = "ok"
    except Exception:
        checks["rabbitmq"] = "unavailable"
        status = "degraded"

    status_code = 200 if status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": status, "checks": checks},
    )
