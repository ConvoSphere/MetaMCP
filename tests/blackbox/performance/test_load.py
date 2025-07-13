"""
Black Box Tests for Load and Performance

Tests the performance characteristics and load handling of MetaMCP container.
"""

import asyncio
import time
import pytest
from httpx import AsyncClient

from ..conftest import API_BASE_URL, TEST_TOOL, assert_success_response


class TestResponseTime:
    """Test response time characteristics."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self, http_client: AsyncClient):
        """Test response time of health endpoints."""
        endpoints = [
            f"{API_BASE_URL}/health",
            f"{API_BASE_URL}/health/detailed",
            f"{API_BASE_URL}/health/ready",
            f"{API_BASE_URL}/health/live"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await http_client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Health endpoints should respond quickly
            assert response_time < 1.0, f"Health endpoint {endpoint} took {response_time:.3f}s, expected < 1.0s"
            assert response.status_code == 200, f"Health endpoint {endpoint} should return 200"
    
    @pytest.mark.asyncio
    async def test_authentication_response_time(self, http_client: AsyncClient):
        """Test response time of authentication endpoints."""
        # Test login response time
        start_time = time.time()
        response = await http_client.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": "test_user", "password": "test_password123"}
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Authentication should be reasonably fast
        assert response_time < 2.0, f"Login took {response_time:.3f}s, expected < 2.0s"
        assert response.status_code in [200, 401], f"Login should return 200 or 401, got {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_tool_operations_response_time(self, authenticated_client: AsyncClient):
        """Test response time of tool operations."""
        # Test tool listing response time
        start_time = time.time()
        response = await authenticated_client.get(f"{API_BASE_URL}/tools")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Tool operations should be reasonably fast
        assert response_time < 3.0, f"Tool listing took {response_time:.3f}s, expected < 3.0s"
        assert response.status_code in [200, 404], f"Tool listing should return 200 or 404, got {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_tool_registration_response_time(self, authenticated_client: AsyncClient):
        """Test response time of tool registration."""
        # Register a test tool
        start_time = time.time()
        response = await authenticated_client.post(
            f"{API_BASE_URL}/tools",
            json=TEST_TOOL
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Tool registration should be reasonably fast
        assert response_time < 5.0, f"Tool registration took {response_time:.3f}s, expected < 5.0s"
        assert response.status_code in [200, 400], f"Tool registration should return 200 or 400, got {response.status_code}"
        
        # Cleanup if successful
        if response.status_code == 200:
            delete_response = await authenticated_client.delete(
                f"{API_BASE_URL}/tools/{TEST_TOOL['name']}"
            )
            assert delete_response.status_code == 200


class TestConcurrentLoad:
    """Test concurrent load handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, http_client: AsyncClient):
        """Test concurrent health check requests."""
        num_requests = 10
        endpoint = f"{API_BASE_URL}/health"
        
        # Create concurrent requests
        tasks = []
        for i in range(num_requests):
            task = http_client.get(endpoint)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Check all requests succeeded
        successful_requests = 0
        for result in results:
            if isinstance(result, Exception):
                continue
            if result.status_code == 200:
                successful_requests += 1
        
        # Should handle concurrent requests well
        assert successful_requests >= num_requests * 0.8, f"Only {successful_requests}/{num_requests} requests succeeded"
        assert total_time < num_requests * 0.5, f"Concurrent requests took {total_time:.3f}s, expected < {num_requests * 0.5}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication(self, http_client: AsyncClient):
        """Test concurrent authentication requests."""
        num_requests = 5
        login_data = {"username": "test_user", "password": "test_password123"}
        
        # Create concurrent login requests
        tasks = []
        for i in range(num_requests):
            task = http_client.post(f"{API_BASE_URL}/auth/login", json=login_data)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Check requests handled
        successful_requests = 0
        for result in results:
            if isinstance(result, Exception):
                continue
            if result.status_code in [200, 401]:
                successful_requests += 1
        
        # Should handle concurrent auth requests
        assert successful_requests >= num_requests * 0.8, f"Only {successful_requests}/{num_requests} auth requests succeeded"
        assert total_time < num_requests * 1.0, f"Concurrent auth took {total_time:.3f}s, expected < {num_requests * 1.0}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self, authenticated_client: AsyncClient):
        """Test concurrent tool operations."""
        num_operations = 5
        
        # Create test tools for concurrent operations
        test_tools = []
        for i in range(num_operations):
            tool = TEST_TOOL.copy()
            tool["name"] = f"test_tool_{i}"
            tool["description"] = f"Test tool {i}"
            test_tools.append(tool)
        
        # Register tools concurrently
        register_tasks = []
        for tool in test_tools:
            task = authenticated_client.post(f"{API_BASE_URL}/tools", json=tool)
            register_tasks.append(task)
        
        start_time = time.time()
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)
        end_time = time.time()
        
        register_time = end_time - start_time
        
        # Check registration results
        successful_registrations = 0
        for result in register_results:
            if isinstance(result, Exception):
                continue
            if result.status_code in [200, 400]:  # 400 for duplicate tools
                successful_registrations += 1
        
        assert successful_registrations >= num_operations * 0.8, f"Only {successful_registrations}/{num_operations} registrations succeeded"
        assert register_time < num_operations * 2.0, f"Concurrent registration took {register_time:.3f}s, expected < {num_operations * 2.0}s"
        
        # Cleanup: Delete tools concurrently
        delete_tasks = []
        for tool in test_tools:
            task = authenticated_client.delete(f"{API_BASE_URL}/tools/{tool['name']}")
            delete_tasks.append(task)
        
        delete_results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # Check cleanup results
        successful_deletions = 0
        for result in delete_results:
            if isinstance(result, Exception):
                continue
            if result.status_code in [200, 404]:  # 404 if tool wasn't registered
                successful_deletions += 1
        
        assert successful_deletions >= num_operations * 0.8, f"Only {successful_deletions}/{num_operations} deletions succeeded"


class TestStressTesting:
    """Test stress conditions."""
    
    @pytest.mark.asyncio
    async def test_rapid_requests(self, http_client: AsyncClient):
        """Test rapid successive requests."""
        endpoint = f"{API_BASE_URL}/health"
        num_requests = 20
        
        # Make rapid successive requests
        start_time = time.time()
        for i in range(num_requests):
            response = await http_client.get(endpoint)
            assert response.status_code == 200, f"Request {i} failed with status {response.status_code}"
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / num_requests
        
        # Should handle rapid requests without significant degradation
        assert avg_time < 0.5, f"Average response time {avg_time:.3f}s too high for rapid requests"
        assert total_time < num_requests * 0.5, f"Total time {total_time:.3f}s too high for {num_requests} requests"
    
    @pytest.mark.asyncio
    async def test_large_payload_handling(self, authenticated_client: AsyncClient):
        """Test handling of large payloads."""
        # Create a large tool definition
        large_tool = TEST_TOOL.copy()
        large_tool["name"] = "large_test_tool"
        large_tool["description"] = "A" * 1000  # Large description
        large_tool["metadata"] = {"large_data": "x" * 5000}  # Large metadata
        
        # Test registration with large payload
        start_time = time.time()
        response = await authenticated_client.post(
            f"{API_BASE_URL}/tools",
            json=large_tool
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should handle large payloads reasonably
        assert response_time < 10.0, f"Large payload registration took {response_time:.3f}s, expected < 10.0s"
        assert response.status_code in [200, 400, 413], f"Large payload should return 200, 400, or 413, got {response.status_code}"
        
        # Cleanup if successful
        if response.status_code == 200:
            delete_response = await authenticated_client.delete(
                f"{API_BASE_URL}/tools/{large_tool['name']}"
            )
            assert delete_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, http_client: AsyncClient):
        """Test memory usage stability over time."""
        endpoint = f"{API_BASE_URL}/health"
        
        # Make many requests to test memory stability
        num_requests = 50
        
        start_time = time.time()
        for i in range(num_requests):
            response = await http_client.get(endpoint)
            assert response.status_code == 200, f"Request {i} failed with status {response.status_code}"
            
            # Small delay to simulate real usage
            await asyncio.sleep(0.1)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Should maintain consistent performance
        avg_time = total_time / num_requests
        assert avg_time < 1.0, f"Average response time {avg_time:.3f}s degraded over time"


class TestResourceUtilization:
    """Test resource utilization characteristics."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_handling(self, http_client: AsyncClient):
        """Test connection pool handling."""
        endpoint = f"{API_BASE_URL}/health"
        
        # Make many requests to test connection pool
        num_requests = 30
        
        start_time = time.time()
        for i in range(num_requests):
            response = await http_client.get(endpoint)
            assert response.status_code == 200, f"Request {i} failed with status {response.status_code}"
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Should handle connection pool efficiently
        avg_time = total_time / num_requests
        assert avg_time < 0.3, f"Connection pool handling degraded: avg time {avg_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, http_client: AsyncClient):
        """Test performance after error conditions."""
        # Make some requests that might fail
        endpoints = [
            f"{API_BASE_URL}/tools/nonexistent_tool",
            f"{API_BASE_URL}/auth/login",
            f"{API_BASE_URL}/health"
        ]
        
        # Test performance after errors
        for endpoint in endpoints:
            start_time = time.time()
            response = await http_client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should handle errors efficiently
            assert response_time < 2.0, f"Error handling took {response_time:.3f}s for {endpoint}"
            
            # Should return appropriate status codes
            assert response.status_code in [200, 401, 404], f"Unexpected status {response.status_code} for {endpoint}" 