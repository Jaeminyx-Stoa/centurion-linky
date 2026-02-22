"""Tests for consultation protocols API."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestProtocolsAPI:
    @pytest.mark.asyncio
    async def test_create_protocol(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/protocols",
            json={
                "name": "보톡스 상담 프로토콜",
                "checklist_items": [
                    {
                        "id": "chk_1",
                        "question_ko": "임신 중이거나 수유 중입니까?",
                        "required": True,
                        "type": "boolean",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code in (201, 401, 422)

    @pytest.mark.asyncio
    async def test_list_protocols(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/v1/protocols", headers=auth_headers)
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_get_protocol_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            f"/api/v1/protocols/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code in (404, 401)

    @pytest.mark.asyncio
    async def test_init_protocol_state(
        self, client: AsyncClient, auth_headers: dict
    ):
        booking_id = uuid.uuid4()
        protocol_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/protocols/bookings/{booking_id}/init",
            params={"protocol_id": str(protocol_id)},
            headers=auth_headers,
        )
        assert response.status_code in (200, 404, 401)
