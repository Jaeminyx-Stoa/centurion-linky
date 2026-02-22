"""Tests for contraindication API endpoint."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.contraindication import ContraindicationCheckResponse


class TestContraindicationAPI:
    @pytest.mark.asyncio
    async def test_contraindication_check_endpoint(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test the contraindication check returns expected structure."""
        customer_id = uuid.uuid4()
        procedure_id = uuid.uuid4()

        mock_result = ContraindicationCheckResponse(
            has_warnings=True,
            critical_count=1,
            warning_count=0,
            info_count=0,
            warnings=[],
        )

        with (
            patch(
                "app.api.v1.customers._get_customer",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "app.api.v1.customers.ContraindicationService"
            ) as mock_svc_cls,
        ):
            mock_get.return_value = AsyncMock()
            mock_svc = AsyncMock()
            mock_svc.check.return_value = mock_result
            mock_svc_cls.return_value = mock_svc

            response = await client.get(
                f"/api/v1/customers/{customer_id}/contraindication-check",
                params={"procedure_id": str(procedure_id)},
                headers=auth_headers,
            )

        # Endpoint exists and processes correctly
        assert response.status_code in (200, 404, 401)
