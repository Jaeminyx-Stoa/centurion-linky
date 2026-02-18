import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import Clinic, MedicalTerm, User


# --- Fixtures ---

@pytest.fixture
async def term_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="용어테스트의원", slug="term-test")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest.fixture
async def term_admin(db: AsyncSession, term_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=term_clinic.id,
        email="admin@term-test.com",
        password_hash=hash_password("password123"),
        name="용어관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def admin_token(term_admin: User) -> str:
    return create_access_token({"sub": str(term_admin.id)})


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


# --- POST /api/v1/medical-terms ---

class TestCreateMedicalTerm:
    async def test_create_term(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/medical-terms",
            json={
                "term_ko": "보톡스",
                "translations": {"ja": "ボトックス", "en": "Botox", "zh-CN": "肉毒素"},
                "category": "procedure",
                "description": "보툴리눔 톡신 시술",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["term_ko"] == "보톡스"
        assert data["translations"]["ja"] == "ボトックス"
        assert data["category"] == "procedure"
        assert data["is_verified"] is False
        assert data["is_active"] is True

    async def test_create_term_minimal(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/medical-terms",
            json={"term_ko": "필러", "category": "material"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["term_ko"] == "필러"
        assert data["translations"] == {}

    async def test_create_rejects_invalid_category(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/medical-terms",
            json={"term_ko": "보톡스", "category": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/medical-terms",
            json={"term_ko": "보톡스", "category": "procedure"},
        )
        assert response.status_code == 401


# --- GET /api/v1/medical-terms ---

class TestListMedicalTerms:
    async def test_list_returns_clinic_and_global_terms(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        term_clinic: Clinic,
    ):
        # Other clinic for FK constraint
        other_clinic = Clinic(id=uuid.uuid4(), name="다른의원", slug="other-clinic")
        db.add(other_clinic)
        await db.commit()

        # Global term (clinic_id=None)
        global_term = MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=None,
            term_ko="보톡스",
            translations={"ja": "ボトックス"},
            category="procedure",
        )
        # Clinic-specific term
        clinic_term = MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=term_clinic.id,
            term_ko="물광주사",
            translations={"ja": "水光注射"},
            category="procedure",
        )
        # Other clinic's term (should NOT appear)
        other_term = MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=other_clinic.id,
            term_ko="리프팅",
            translations={},
            category="procedure",
        )
        db.add_all([global_term, clinic_term, other_term])
        await db.commit()

        response = await client.get(
            "/api/v1/medical-terms", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        term_names = [t["term_ko"] for t in data]
        assert "보톡스" in term_names       # global
        assert "물광주사" in term_names     # own clinic
        assert "리프팅" not in term_names   # other clinic

    async def test_list_filters_by_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        term_clinic: Clinic,
    ):
        for ko, cat in [("보톡스", "procedure"), ("두통", "symptom")]:
            db.add(MedicalTerm(
                id=uuid.uuid4(),
                clinic_id=term_clinic.id,
                term_ko=ko,
                translations={},
                category=cat,
            ))
        await db.commit()

        response = await client.get(
            "/api/v1/medical-terms?category=procedure",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(t["category"] == "procedure" for t in data)

    async def test_list_search_by_keyword(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        term_clinic: Clinic,
    ):
        db.add(MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=term_clinic.id,
            term_ko="보톡스",
            translations={"en": "Botox"},
            category="procedure",
        ))
        await db.commit()

        response = await client.get(
            "/api/v1/medical-terms?q=보톡",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["term_ko"] == "보톡스"


# --- GET /api/v1/medical-terms/{id} ---

class TestGetMedicalTerm:
    async def test_get_term(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        term_clinic: Clinic,
    ):
        term = MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=term_clinic.id,
            term_ko="보톡스",
            translations={"ja": "ボトックス"},
            category="procedure",
        )
        db.add(term)
        await db.commit()

        response = await client.get(
            f"/api/v1/medical-terms/{term.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["term_ko"] == "보톡스"

    async def test_get_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            f"/api/v1/medical-terms/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# --- PATCH /api/v1/medical-terms/{id} ---

class TestUpdateMedicalTerm:
    async def test_update_term(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        term_clinic: Clinic,
    ):
        term = MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=term_clinic.id,
            term_ko="보톡스",
            translations={"ja": "ボトックス"},
            category="procedure",
        )
        db.add(term)
        await db.commit()

        response = await client.patch(
            f"/api/v1/medical-terms/{term.id}",
            json={
                "translations": {"ja": "ボトックス", "en": "Botox"},
                "is_verified": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translations"]["en"] == "Botox"
        assert data["is_verified"] is True

    async def test_update_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.patch(
            f"/api/v1/medical-terms/{uuid.uuid4()}",
            json={"term_ko": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


# --- DELETE /api/v1/medical-terms/{id} ---

class TestDeleteMedicalTerm:
    async def test_delete_term(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        term_clinic: Clinic,
    ):
        term = MedicalTerm(
            id=uuid.uuid4(),
            clinic_id=term_clinic.id,
            term_ko="삭제될용어",
            translations={},
            category="general",
        )
        db.add(term)
        await db.commit()

        response = await client.delete(
            f"/api/v1/medical-terms/{term.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.delete(
            f"/api/v1/medical-terms/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404
