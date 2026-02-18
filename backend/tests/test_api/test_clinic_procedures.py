import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.clinic_procedure import ClinicProcedure
from app.models.procedure import Procedure
from app.models.procedure_category import ProcedureCategory
from app.models.user import User


@pytest_asyncio.fixture
async def cp_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="클리닉시술의원", slug="cp-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def cp_admin(db: AsyncSession, cp_clinic: Clinic) -> User:
    from app.core.security import hash_password

    user = User(
        id=uuid.uuid4(),
        clinic_id=cp_clinic.id,
        email="cp-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="클리닉관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def cp_token(client: AsyncClient, cp_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "cp-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def auth_headers(cp_token: str) -> dict:
    return {"Authorization": f"Bearer {cp_token}"}


@pytest_asyncio.fixture
async def cp_category(db: AsyncSession) -> ProcedureCategory:
    cat = ProcedureCategory(
        id=uuid.uuid4(),
        name_ko="주사시술",
        slug="cp-injection",
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@pytest_asyncio.fixture
async def cp_procedure(
    db: AsyncSession, cp_category: ProcedureCategory
) -> Procedure:
    proc = Procedure(
        id=uuid.uuid4(),
        category_id=cp_category.id,
        name_ko="보톡스",
        name_en="Botox",
        slug="cp-botox",
        description_ko="보툴리눔 톡신 시술",
        effects_ko="주름 개선",
        duration_minutes=30,
        effect_duration="3~6개월",
        downtime_days=0,
        min_interval_days=90,
        precautions_before="음주 삼가",
        precautions_during="None",
        precautions_after="사우나 금지",
        pain_level=3,
        anesthesia_options="크림 마취",
    )
    db.add(proc)
    await db.commit()
    await db.refresh(proc)
    return proc


@pytest_asyncio.fixture
async def clinic_procedure(
    db: AsyncSession, cp_clinic: Clinic, cp_procedure: Procedure
) -> ClinicProcedure:
    cp = ClinicProcedure(
        id=uuid.uuid4(),
        clinic_id=cp_clinic.id,
        procedure_id=cp_procedure.id,
        custom_duration_minutes=20,
        custom_pain_level=2,
        material_cost=5000,
        difficulty_score=2,
        clinic_preference=1,
    )
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp


class TestCreateClinicProcedure:
    @pytest.mark.asyncio
    async def test_create(
        self,
        client: AsyncClient,
        auth_headers: dict,
        cp_procedure: Procedure,
    ):
        resp = await client.post(
            "/api/v1/clinic-procedures",
            json={
                "procedure_id": str(cp_procedure.id),
                "custom_duration_minutes": 25,
                "material_cost": "8000.00",
                "difficulty_score": 3,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["procedure_id"] == str(cp_procedure.id)
        assert data["custom_duration_minutes"] == 25
        assert data["difficulty_score"] == 3

    @pytest.mark.asyncio
    async def test_create_duplicate_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
        cp_procedure: Procedure,
    ):
        resp = await client.post(
            "/api/v1/clinic-procedures",
            json={"procedure_id": str(cp_procedure.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestListClinicProcedures:
    @pytest.mark.asyncio
    async def test_list_own_clinic(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
    ):
        resp = await client.get(
            "/api/v1/clinic-procedures",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["custom_duration_minutes"] == 20


class TestGetClinicProcedureMerged:
    @pytest.mark.asyncio
    async def test_get_merged(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
    ):
        resp = await client.get(
            f"/api/v1/clinic-procedures/{clinic_procedure.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["procedure_name_ko"] == "보톡스"

        # Custom overridden fields
        assert data["duration_minutes"]["value"] == 20
        assert data["duration_minutes"]["source"] == "custom"
        assert data["duration_minutes"]["default_value"] == 30

        assert data["pain_level"]["value"] == 2
        assert data["pain_level"]["source"] == "custom"

        # Default fields (not overridden)
        assert data["description"]["value"] == "보툴리눔 톡신 시술"
        assert data["description"]["source"] == "default"

        assert data["effect_duration"]["value"] == "3~6개월"
        assert data["effect_duration"]["source"] == "default"

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.get(
            f"/api/v1/clinic-procedures/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestUpdateClinicProcedure:
    @pytest.mark.asyncio
    async def test_update_custom_fields(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
    ):
        resp = await client.patch(
            f"/api/v1/clinic-procedures/{clinic_procedure.id}",
            json={
                "custom_description": "우리 클리닉만의 보톡스",
                "difficulty_score": 1,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["custom_description"] == "우리 클리닉만의 보톡스"
        assert data["difficulty_score"] == 1
        # Unchanged fields preserved
        assert data["custom_duration_minutes"] == 20


class TestResetField:
    @pytest.mark.asyncio
    async def test_reset_to_default(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
    ):
        resp = await client.post(
            f"/api/v1/clinic-procedures/{clinic_procedure.id}/reset/duration_minutes",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # After reset, duration_minutes should come from default
        assert data["duration_minutes"]["source"] == "default"
        assert data["duration_minutes"]["value"] == 30

    @pytest.mark.asyncio
    async def test_reset_invalid_field(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
    ):
        resp = await client.post(
            f"/api/v1/clinic-procedures/{clinic_procedure.id}/reset/invalid_field",
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestDeleteClinicProcedure:
    @pytest.mark.asyncio
    async def test_deactivate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        clinic_procedure: ClinicProcedure,
    ):
        resp = await client.delete(
            f"/api/v1/clinic-procedures/{clinic_procedure.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
