"""Tests for Response Library CRUD API."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.clinic import Clinic
from app.models.response_library import ResponseLibrary
from app.models.user import User


@pytest.fixture
async def auth_token(test_user: User) -> str:
    return create_access_token({"sub": str(test_user.id), "clinic_id": str(test_user.clinic_id)})


@pytest.fixture
async def sample_entry(db: AsyncSession, test_clinic: Clinic) -> ResponseLibrary:
    entry = ResponseLibrary(
        id=uuid.uuid4(),
        clinic_id=test_clinic.id,
        category="pricing",
        question="보톡스 가격?",
        answer="10만원부터",
        language_code="ko",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@pytest.mark.asyncio
async def test_create_response_library(client: AsyncClient, auth_token: str):
    resp = await client.post(
        "/api/v1/response-library",
        json={
            "category": "pricing",
            "question": "필러 가격?",
            "answer": "20만원부터",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "pricing"
    assert data["question"] == "필러 가격?"
    assert data["answer"] == "20만원부터"
    assert data["language_code"] == "ko"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_with_tags(client: AsyncClient, auth_token: str):
    resp = await client.post(
        "/api/v1/response-library",
        json={
            "category": "procedure",
            "question": "보톡스 시간?",
            "answer": "20분",
            "tags": ["보톡스", "시간"],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["tags"] == ["보톡스", "시간"]


@pytest.mark.asyncio
async def test_create_invalid_category(client: AsyncClient, auth_token: str):
    resp = await client.post(
        "/api/v1/response-library",
        json={
            "category": "invalid_category",
            "question": "test",
            "answer": "test",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_response_library(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.get(
        "/api/v1/response-library",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["category"] == "pricing"


@pytest.mark.asyncio
async def test_list_filter_by_category(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.get(
        "/api/v1/response-library?category=pricing",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    assert all(e["category"] == "pricing" for e in resp.json())


@pytest.mark.asyncio
async def test_list_filter_by_query(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.get(
        "/api/v1/response-library?q=보톡스",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_single_entry(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.get(
        f"/api/v1/response-library/{sample_entry.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == str(sample_entry.id)


@pytest.mark.asyncio
async def test_get_nonexistent_entry(client: AsyncClient, auth_token: str):
    fake_id = uuid.uuid4()
    resp = await client.get(
        f"/api/v1/response-library/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_response_library(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.patch(
        f"/api/v1/response-library/{sample_entry.id}",
        json={"answer": "15만원부터", "tags": ["updated"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "15만원부터"
    assert data["tags"] == ["updated"]


@pytest.mark.asyncio
async def test_deactivate_entry(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.patch(
        f"/api/v1/response-library/{sample_entry.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_response_library(
    client: AsyncClient, auth_token: str, sample_entry: ResponseLibrary
):
    resp = await client.delete(
        f"/api/v1/response-library/{sample_entry.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 204

    # Verify deleted
    resp2 = await client.get(
        f"/api/v1/response-library/{sample_entry.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, sample_entry: ResponseLibrary):
    resp = await client.get("/api/v1/response-library")
    assert resp.status_code in (401, 403)
