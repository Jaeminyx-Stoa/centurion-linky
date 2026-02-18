from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.api.webhooks.kakao import router as kakao_webhook_router
from app.api.webhooks.line import router as line_webhook_router
from app.api.webhooks.meta import router as meta_webhook_router
from app.api.webhooks.payments import router as payment_webhook_router
from app.api.webhooks.telegram import router as telegram_webhook_router
from app.config import settings
from app.websocket.endpoint import router as ws_router

app = FastAPI(
    title="Medical Messenger MVP",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
app.include_router(telegram_webhook_router, prefix="/api")
app.include_router(meta_webhook_router, prefix="/api")
app.include_router(line_webhook_router, prefix="/api")
app.include_router(kakao_webhook_router, prefix="/api")
app.include_router(payment_webhook_router, prefix="/api")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
