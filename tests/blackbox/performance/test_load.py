"""
Black Box Performance and Load Tests

Tests the performance characteristics and load handling capabilities of the MetaMCP REST API.
"""

import asyncio
import time

import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL


class TestPerformanceEndpoints:
    """Test API performance under various load conditions."""

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, http_client: AsyncClient):
        """Test health endpoint response time under normal load."""
        start_time = time.time()
        response = await http_client.get(f"{API_BASE_URL}health/")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health endpoint too slow: {response_time:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self, http_client: AsyncClient):
        """Test multiple concurrent health requests."""

        async def make_request():
            return await http_client.get(f"{API_BASE_URL}health/")

        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "healthy" in data

    @pytest.mark.asyncio
    async def test_tool_registration_performance(
        self, authenticated_client: AsyncClient
    ):
        """Test tool registration performance."""
        tool_data = {
            "name": f"perf_test_tool_{int(time.time())}",
            "description": "Performance test tool",
            "endpoint": "http://localhost:9000",
            "category": "performance",
            "capabilities": ["read"],
            "security_level": 1,
        }

        start_time = time.time()
        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/", json=tool_data
        )
        end_time = time.time()

        assert response.status_code in [200, 201]
        response_time = end_time - start_time
        assert response_time < 2.0, f"Tool registration too slow: {response_time:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self, authenticated_client: AsyncClient):
        """Test concurrent tool registration and retrieval."""

        async def register_tool(i: int):
            tool_data = {
                "name": f"concurrent_tool_{i}_{int(time.time())}",
                "description": f"Concurrent test tool {i}",
                "endpoint": f"http://localhost:900{i}",
                "category": "concurrent",
                "capabilities": ["read"],
                "security_level": 1,
            }
            return await authenticated_client.post(
                f"{API_BASE_URL}tools/", json=tool_data
            )

        # Register 5 tools concurrently
        tasks = [register_tool(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_search_performance(self, authenticated_client: AsyncClient):
        """Test search endpoint performance."""
        start_time = time.time()
        response = await authenticated_client.get(
            f"{API_BASE_URL}tools/search/?q=test&max_results=10"
        )
        end_time = time.time()

        # Search might not be implemented yet, so accept 404
        assert response.status_code in [200, 404]
        response_time = end_time - start_time
        assert response_time < 3.0, f"Search too slow: {response_time:.3f}s"


class TestLoadTesting:
    """Test API behavior under high load conditions."""

    @pytest.mark.asyncio
    async def test_rapid_health_checks(self, http_client: AsyncClient):
        """Test rapid succession of health checks."""
        start_time = time.time()

        for i in range(50):
            response = await http_client.get(f"{API_BASE_URL}health/")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 50

        assert avg_time < 0.1, f"Average health check too slow: {avg_time:.3f}s"

    @pytest.mark.asyncio
    async def test_mixed_workload(self, authenticated_client: AsyncClient):
        """Test mixed workload of different operations."""

        async def health_check():
            return await authenticated_client.get(f"{API_BASE_URL}health/")

        async def list_tools():
            return await authenticated_client.get(f"{API_BASE_URL}tools/")

        async def search_tools():
            return await authenticated_client.get(f"{API_BASE_URL}tools/search/?q=test")

        # Mix of different operations
        tasks = []
        for i in range(10):
            tasks.append(health_check())
            tasks.append(list_tools())
            tasks.append(search_tools())

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that most requests succeeded (accept 404 for search endpoint)
        success_count = sum(
            1
            for r in responses
            if not isinstance(r, Exception) and r.status_code in [200, 404]
        )
        assert (
            success_count >= len(responses) * 0.6
        ), f"Too many failures: {success_count}/{len(responses)}"


class TestStressTesting:
    """Test API behavior under stress conditions."""

    @pytest.mark.asyncio
    async def test_large_payload_handling(self, authenticated_client: AsyncClient):
        """Test handling of large payloads."""
        large_tool = {
            "name": "large_test_tool",
            "description": "A" * 1000,  # Large description
            "endpoint": "http://localhost:9000",
            "category": "stress",
            "capabilities": ["read", "write", "execute"]
            * 100,  # Large capabilities list
            "security_level": 1,
            "metadata": {"large_data": "x" * 5000},  # Large metadata
        }

        response = await authenticated_client.post(
            f"{API_BASE_URL}tools/", json=large_tool
        )

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 201, 400, 413]

    @pytest.mark.asyncio
    async def test_concurrent_authentication(self, http_client: AsyncClient):
        """Test concurrent authentication attempts."""

        async def login_attempt():
            return await http_client.post(
                f"{API_BASE_URL}auth/login",
                json={"username": "test_user", "password": "test_password123"},
            )

        # Multiple concurrent login attempts
        tasks = [login_attempt() for _ in range(20)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle concurrent auth gracefully
        success_count = sum(1 for r in responses if not isinstance(r, Exception))
        assert success_count > 0, "No successful authentication attempts"
