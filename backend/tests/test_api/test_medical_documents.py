import uuid
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.customer import Customer
from app.models.medical_document import MedicalDocument
from app.models.user import User


@pytest_asyncio.fixture
async def md_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="문서API의원", slug="md-api-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def md_admin(db: AsyncSession, md_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=md_clinic.id,
        email="md-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="문서관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def md_token(client: AsyncClient, md_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "md-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def md_headers(md_token: str) -> dict:
    return {"Authorization": f"Bearer {md_token}"}


@pytest_asyncio.fixture
async def md_customer(db: AsyncSession, md_clinic: Clinic) -> Customer:
    customer = Customer(
        id=uuid.uuid4(),
        clinic_id=md_clinic.id,
        messenger_type="telegram",
        messenger_user_id="md-tg-1",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def md_document(
    db: AsyncSession, md_clinic: Clinic, md_customer: Customer
) -> MedicalDocument:
    doc = MedicalDocument(
        id=uuid.uuid4(),
        clinic_id=md_clinic.id,
        customer_id=md_customer.id,
        document_type="chart_draft",
        title="Test Chart Draft",
        content={"chief_complaint": "test", "desired_procedures": ["botox"]},
        status="draft",
        generated_by="ai",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


class TestListDocuments:
    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient, md_headers: dict):
        resp = await client.get("/api/v1/medical-documents/", headers=md_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_with_document(
        self, client: AsyncClient, md_headers: dict, md_document: MedicalDocument
    ):
        resp = await client.get("/api/v1/medical-documents/", headers=md_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["document_type"] == "chart_draft"


class TestGetDocument:
    @pytest.mark.asyncio
    async def test_get_existing(
        self, client: AsyncClient, md_headers: dict, md_document: MedicalDocument
    ):
        resp = await client.get(
            f"/api/v1/medical-documents/{md_document.id}", headers=md_headers
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Chart Draft"

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, md_headers: dict):
        resp = await client.get(
            f"/api/v1/medical-documents/{uuid.uuid4()}", headers=md_headers
        )
        assert resp.status_code == 404


class TestUpdateDocumentStatus:
    @pytest.mark.asyncio
    async def test_update_to_reviewed(
        self, client: AsyncClient, md_headers: dict, md_document: MedicalDocument
    ):
        resp = await client.patch(
            f"/api/v1/medical-documents/{md_document.id}/status",
            json={"status": "reviewed"},
            headers=md_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "reviewed"
        assert resp.json()["reviewed_at"] is not None


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_existing(
        self, client: AsyncClient, md_headers: dict, md_document: MedicalDocument
    ):
        resp = await client.delete(
            f"/api/v1/medical-documents/{md_document.id}", headers=md_headers
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client: AsyncClient, md_headers: dict):
        resp = await client.delete(
            f"/api/v1/medical-documents/{uuid.uuid4()}", headers=md_headers
        )
        assert resp.status_code == 404
