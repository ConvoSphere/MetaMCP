"""
Black Box Tests for Composition API Endpoints

Tests the workflow registration and listing endpoints of the MetaMCP REST API.
"""

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL

WORKFLOW = {
    "id": "test_workflow_1",
    "name": "Test Workflow",
    "description": "A test workflow for blackbox testing.",
    "steps": [
        {"tool": "test_calculator", "input": {"operation": "add", "a": 1, "b": 2}}
    ],
}


class TestCompositionEndpoints:
    """Test workflow registration and listing endpoints."""

    @pytest.mark.asyncio
    async def test_register_workflow(self, authenticated_client: AsyncClient):
        """Test registering a new workflow."""
        request_data = {"workflow": WORKFLOW}
        response = await authenticated_client.post(
            f"{API_BASE_URL}composition/workflows", json=request_data
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "workflow_id" in data
        assert "message" in data
        assert "registered successfully" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_list_workflows(self, authenticated_client: AsyncClient):
        """Test listing all registered workflows."""
        response = await authenticated_client.get(
            f"{API_BASE_URL}composition/workflows"
        )
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "total_count" in data
        assert isinstance(data["workflows"], list)

    @pytest.mark.asyncio
    async def test_register_workflow_unauthorized(self, http_client: AsyncClient):
        """Test registering a workflow without authentication (should fail)."""
        request_data = {"workflow": WORKFLOW}
        response = await http_client.post(
            f"{API_BASE_URL}composition/workflows", json=request_data
        )
        assert response.status_code in [401, 403]
        data = response.json()
        assert "error" in data or "detail" in data
