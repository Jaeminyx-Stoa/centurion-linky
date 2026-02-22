from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.ab_tests import router as ab_tests_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit import router as audit_router
from app.api.v1.ai_personas import router as ai_personas_router
from app.api.v1.auth import router as auth_router
from app.api.v1.clinics import router as clinics_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.crm import router as crm_router
from app.api.v1.customers import router as customers_router
from app.api.v1.llm_usage import router as llm_usage_router
from app.api.v1.medical_terms import router as medical_terms_router
from app.api.v1.messenger_accounts import router as messenger_accounts_router
from app.api.v1.clinic_procedures import router as clinic_procedures_router
from app.api.v1.packages import router as packages_router
from app.api.v1.protocols import router as protocols_router
from app.api.v1.payment_settings import router as payment_settings_router
from app.api.v1.payments import router as payments_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.satisfaction import router as satisfaction_router
from app.api.v1.settlements import router as settlements_router
from app.api.v1.simulations import router as simulations_router
from app.api.v1.procedure_categories import router as procedure_categories_router
from app.api.v1.procedures import router as procedures_router
from app.api.v1.response_library import router as response_library_router
from app.api.v1.uploads import router as uploads_router

router = APIRouter(prefix="/api/v1")
router.include_router(admin_router)
router.include_router(ab_tests_router)
router.include_router(ai_personas_router)
router.include_router(audit_router)
router.include_router(analytics_router)
router.include_router(auth_router)
router.include_router(bookings_router)
router.include_router(clinics_router)
router.include_router(clinic_procedures_router)
router.include_router(packages_router)
router.include_router(protocols_router)
router.include_router(conversations_router)
router.include_router(crm_router)
router.include_router(customers_router)
router.include_router(llm_usage_router)
router.include_router(medical_terms_router)
router.include_router(messenger_accounts_router)
router.include_router(payment_settings_router)
router.include_router(payments_router)
router.include_router(pricing_router)
router.include_router(satisfaction_router)
router.include_router(settlements_router)
router.include_router(simulations_router)
router.include_router(procedure_categories_router)
router.include_router(procedures_router)
router.include_router(response_library_router)
router.include_router(uploads_router)
