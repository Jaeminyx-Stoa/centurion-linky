from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.medical_terms import router as medical_terms_router
from app.api.v1.messenger_accounts import router as messenger_accounts_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(medical_terms_router)
router.include_router(messenger_accounts_router)
