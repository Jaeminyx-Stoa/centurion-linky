import uuid
from datetime import date, time
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.medical_document import MedicalDocument
from app.models.messenger_account import MessengerAccount
from app.models.message import Message
from app.models.procedure import Procedure
from app.services.medical_document_service import MedicalDocumentService


@pytest_asyncio.fixture
async def doc_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="문서의원", slug="doc-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def doc_customer(db: AsyncSession, doc_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=doc_clinic.id,
        messenger_type="telegram",
        messenger_user_id="doc-tg-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def doc_messenger(db: AsyncSession, doc_clinic: Clinic) -> MessengerAccount:
    account = MessengerAccount(
        id=uuid.uuid4(),
        clinic_id=doc_clinic.id,
        messenger_type="telegram",
        account_name="test-bot",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def doc_conversation(
    db: AsyncSession, doc_clinic: Clinic, doc_customer: Customer, doc_messenger: MessengerAccount
) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        clinic_id=doc_clinic.id,
        customer_id=doc_customer.id,
        messenger_account_id=doc_messenger.id,
        status="active",
    )
    db.add(conv)
    # Add some messages
    for i, content in enumerate(
        ["안녕하세요, 보톡스 상담 받고 싶어요", "어떤 부위를 원하시나요?", "이마와 미간 부위요"]
    ):
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            clinic_id=doc_clinic.id,
            sender_type="customer" if i % 2 == 0 else "ai",
            content=content,
            content_type="text",
            messenger_type="telegram",
        )
        db.add(msg)
    await db.commit()
    await db.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def doc_procedure(db: AsyncSession) -> Procedure:
    proc = Procedure(
        id=uuid.uuid4(),
        name_ko="보톡스",
        name_en="Botox",
        slug="botox-doc",
        description_ko="주름 개선 시술",
        common_side_effects="멍, 부기",
        precautions_after="시술 후 4시간 동안 눕지 마세요",
        downtime_days=1,
    )
    db.add(proc)
    await db.commit()
    await db.refresh(proc)
    return proc


@pytest_asyncio.fixture
async def doc_booking(
    db: AsyncSession,
    doc_clinic: Clinic,
    doc_customer: Customer,
    doc_procedure: Procedure,
) -> Booking:
    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=doc_clinic.id,
        procedure_id=doc_procedure.id,
    )
    db.add(cp)
    await db.flush()

    booking = Booking(
        id=uuid.uuid4(),
        clinic_id=doc_clinic.id,
        customer_id=doc_customer.id,
        clinic_procedure_id=cp.id,
        booking_date=date(2026, 7, 1),
        booking_time=time(10, 0),
        status="confirmed",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


class TestGenerateChartDraft:
    @pytest.mark.asyncio
    @patch("app.services.medical_document_service.MedicalDocumentService._call_llm")
    async def test_creates_chart_draft(
        self,
        mock_llm: AsyncMock,
        db: AsyncSession,
        doc_clinic: Clinic,
        doc_conversation: Conversation,
    ):
        mock_llm.return_value = {
            "chief_complaint": "이마 주름 개선",
            "desired_procedures": ["보톡스"],
            "medical_history": None,
            "allergies": None,
            "medications": None,
            "skin_type": None,
            "ai_recommendations": "이마 보톡스 추천",
            "notes": None,
        }

        svc = MedicalDocumentService(db)
        doc = await svc.generate_chart_draft(doc_conversation.id, doc_clinic.id)

        assert doc.document_type == "chart_draft"
        assert doc.status == "draft"
        assert doc.generated_by == "ai"
        assert doc.content is not None
        assert doc.content["chief_complaint"] == "이마 주름 개선"

    @pytest.mark.asyncio
    async def test_nonexistent_conversation_raises(self, db: AsyncSession, doc_clinic: Clinic):
        svc = MedicalDocumentService(db)
        with pytest.raises(Exception):
            await svc.generate_chart_draft(uuid.uuid4(), doc_clinic.id)


class TestGenerateConsentForm:
    @pytest.mark.asyncio
    @patch("app.services.medical_document_service.MedicalDocumentService._call_llm")
    async def test_creates_consent_form(
        self,
        mock_llm: AsyncMock,
        db: AsyncSession,
        doc_clinic: Clinic,
        doc_booking: Booking,
    ):
        mock_llm.return_value = {
            "procedure_name": "보톡스",
            "procedure_description": "주름 개선 시술",
            "risks": ["멍", "부기"],
            "alternatives": "필러",
            "expected_results": "주름 감소",
            "aftercare_instructions": "4시간 동안 눕지 마세요",
            "patient_acknowledgements": ["위험성을 이해했습니다"],
        }

        svc = MedicalDocumentService(db)
        doc = await svc.generate_consent_form(doc_booking.id, doc_clinic.id, "ko")

        assert doc.document_type == "consent_form"
        assert doc.language == "ko"
        assert doc.status == "draft"
        assert doc.content["procedure_name"] == "보톡스"

    @pytest.mark.asyncio
    async def test_nonexistent_booking_raises(self, db: AsyncSession, doc_clinic: Clinic):
        svc = MedicalDocumentService(db)
        with pytest.raises(Exception):
            await svc.generate_consent_form(uuid.uuid4(), doc_clinic.id)


class TestListDocuments:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, db: AsyncSession, doc_clinic: Clinic, doc_customer: Customer):
        doc = MedicalDocument(
            id=uuid.uuid4(),
            clinic_id=doc_clinic.id,
            customer_id=doc_customer.id,
            document_type="chart_draft",
            title="Test Chart",
            content={"notes": "test"},
            status="draft",
            generated_by="staff",
        )
        db.add(doc)
        await db.commit()

        svc = MedicalDocumentService(db)
        docs, total = await svc.list_documents(doc_clinic.id)
        assert total == 1
        assert len(docs) == 1
        assert docs[0].title == "Test Chart"

    @pytest.mark.asyncio
    async def test_filter_by_type(self, db: AsyncSession, doc_clinic: Clinic, doc_customer: Customer):
        for doc_type in ["chart_draft", "consent_form"]:
            doc = MedicalDocument(
                id=uuid.uuid4(),
                clinic_id=doc_clinic.id,
                customer_id=doc_customer.id,
                document_type=doc_type,
                title=f"Test {doc_type}",
                status="draft",
                generated_by="ai",
            )
            db.add(doc)
        await db.commit()

        svc = MedicalDocumentService(db)
        docs, total = await svc.list_documents(doc_clinic.id, document_type="chart_draft")
        assert total == 1


class TestUpdateStatus:
    @pytest.mark.asyncio
    async def test_updates_status(self, db: AsyncSession, doc_clinic: Clinic, doc_customer: Customer):
        doc = MedicalDocument(
            id=uuid.uuid4(),
            clinic_id=doc_clinic.id,
            customer_id=doc_customer.id,
            document_type="chart_draft",
            title="Test",
            status="draft",
            generated_by="ai",
        )
        db.add(doc)
        await db.commit()

        svc = MedicalDocumentService(db)
        updated = await svc.update_status(doc.id, doc_clinic.id, "reviewed")
        assert updated.status == "reviewed"
