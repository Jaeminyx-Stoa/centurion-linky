from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.api.webhooks.telegram import router as telegram_webhook_router
from app.config import settings

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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
