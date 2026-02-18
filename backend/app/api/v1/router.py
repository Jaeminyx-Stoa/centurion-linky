from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.customers import router as customers_router
from app.api.v1.medical_terms import router as medical_terms_router
from app.api.v1.messenger_accounts import router as messenger_accounts_router
from app.api.v1.clinic_procedures import router as clinic_procedures_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.procedure_categories import router as procedure_categories_router
from app.api.v1.procedures import router as procedures_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(clinic_procedures_router)
router.include_router(conversations_router)
router.include_router(customers_router)
router.include_router(medical_terms_router)
router.include_router(messenger_accounts_router)
router.include_router(pricing_router)
router.include_router(procedure_categories_router)
router.include_router(procedures_router)
