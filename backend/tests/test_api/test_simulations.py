import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.user import User


# --- Fixtures ---
@pytest_asyncio.fixture
async def sim_clinic(db: AsyncSession) -> Clinic:
    clinic = Clinic(id=uuid.uuid4(), name="시뮬레이션의원", slug="sim-clinic")
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@pytest_asyncio.fixture
async def sim_admin(db: AsyncSession, sim_clinic: Clinic) -> User:
    user = User(
        id=uuid.uuid4(),
        clinic_id=sim_clinic.id,
        email="sim-admin@test.com",
        password_hash=hash_password("pw1234"),
        name="시뮬관리자",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def sim_token(client: AsyncClient, sim_admin: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "sim-admin@test.com", "password": "pw1234"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def sim_headers(sim_token: str) -> dict:
    return {"Authorization": f"Bearer {sim_token}"}


# --- Tests ---
class TestListPersonas:
    @pytest.mark.asyncio
    async def test_list_personas(self, client: AsyncClient):
        resp = await client.get("/api/v1/simulations/personas")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        assert data[0]["name"] == "유코"


class TestCreateSession:
    @pytest.mark.asyncio
    async def test_create(self, client: AsyncClient, sim_headers: dict):
        resp = await client.post(
            "/api/v1/simulations",
            json={
                "persona_name": "유코",
                "persona_config": {"language": "ja", "country": "JP"},
                "max_rounds": 15,
            },
            headers=sim_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["persona_name"] == "유코"
        assert data["status"] == "pending"
        assert data["max_rounds"] == 15


class TestListSessions:
    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient, sim_headers: dict):
        resp = await client.get(
            "/api/v1/simulations", headers=sim_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_with_filter(
        self, client: AsyncClient, sim_headers: dict
    ):
        await client.post(
            "/api/v1/simulations",
            json={"persona_name": "웨이"},
            headers=sim_headers,
        )
        resp = await client.get(
            "/api/v1/simulations?status=pending", headers=sim_headers
        )
        assert len(resp.json()) == 1


class TestGetSession:
    @pytest.mark.asyncio
    async def test_get(self, client: AsyncClient, sim_headers: dict):
        create_resp = await client.post(
            "/api/v1/simulations",
            json={"persona_name": "제시카"},
            headers=sim_headers,
        )
        sid = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/simulations/{sid}", headers=sim_headers
        )
        assert resp.status_code == 200
        assert resp.json()["persona_name"] == "제시카"

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient, sim_headers: dict):
        resp = await client.get(
            f"/api/v1/simulations/{uuid.uuid4()}", headers=sim_headers
        )
        assert resp.status_code == 404


class TestCompleteSession:
    @pytest.mark.asyncio
    async def test_complete_with_booking(
        self, client: AsyncClient, sim_headers: dict, db: AsyncSession
    ):
        # Create session
        create_resp = await client.post(
            "/api/v1/simulations",
            json={"persona_name": "유코"},
            headers=sim_headers,
        )
        sid = create_resp.json()["id"]

        # Manually set messages (simulating completed simulation)
        from app.models.simulation import SimulationSession
        from sqlalchemy import select

        # Use a separate session to set messages
        from tests.conftest import test_session_factory

        async with test_session_factory() as sess:
            result = await sess.execute(
                select(SimulationSession).where(SimulationSession.id == uuid.UUID(sid))
            )
            session = result.scalar_one()
            session.messages = [
                {"role": "customer", "content": "보톡스 가격이 얼마인가요?", "round": 1},
                {"role": "ai", "content": "10만원입니다", "round": 1},
                {"role": "customer", "content": "좋아요 예약할게요!", "round": 2},
            ]
            session.status = "running"
            await sess.commit()

        # Complete
        resp = await client.post(
            f"/api/v1/simulations/{sid}/complete", headers=sim_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["result"] is not None
        assert data["result"]["booked"] is True

    @pytest.mark.asyncio
    async def test_complete_abandoned(
        self, client: AsyncClient, sim_headers: dict
    ):
        create_resp = await client.post(
            "/api/v1/simulations",
            json={"persona_name": "웨이"},
            headers=sim_headers,
        )
        sid = create_resp.json()["id"]

        # Set abandoned messages
        from app.models.simulation import SimulationSession
        from sqlalchemy import select
        from tests.conftest import test_session_factory

        async with test_session_factory() as sess:
            result = await sess.execute(
                select(SimulationSession).where(SimulationSession.id == uuid.UUID(sid))
            )
            session = result.scalar_one()
            session.messages = [
                {"role": "customer", "content": "가격이 얼마인가요?", "round": 1},
                {"role": "ai", "content": "50만원입니다", "round": 1},
                {"role": "customer", "content": "됐어요 비싸요", "round": 2},
            ]
            await sess.commit()

        resp = await client.post(
            f"/api/v1/simulations/{sid}/complete", headers=sim_headers
        )
        assert resp.status_code == 200
        assert resp.json()["result"]["booked"] is False
        assert resp.json()["result"]["abandoned"] is True
