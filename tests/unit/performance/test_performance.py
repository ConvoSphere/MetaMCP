"""
Performance Tests for MetaMCP

These tests measure performance characteristics including:
- Response times for various operations
- Throughput under different load conditions
- Resource usage (memory, CPU)
- Scalability with increasing load
- Performance regression detection
"""

import asyncio
import statistics
import time

import psutil
import pytest
import pytest_asyncio

from metamcp.services.auth_service import AuthService
from metamcp.services.search_service import SearchService
from metamcp.services.tool_service import ToolService
from metamcp.utils.cache import Cache
from metamcp.utils.circuit_breaker import CircuitBreaker
from metamcp.utils.rate_limiter import RateLimiter


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest_asyncio.fixture
    async def setup_performance_services(self, test_settings):
        """Set up services for performance testing."""
        self.auth_service = AuthService(settings=test_settings)
        self.tool_service = ToolService(settings=test_settings)
        self.search_service = SearchService(settings=test_settings)
        self.cache = Cache(settings=test_settings)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.rate_limiter = RateLimiter(settings=test_settings)

        # Create test user
        self.test_user = await self.auth_service.create_user(
            {
                "username": "perf_user",
                "email": "perf@example.com",
                "password": "password123",
                "full_name": "Performance User",
                "is_active": True,
                "is_admin": False,
            }
        )

        yield

        # Cleanup
        await self._cleanup_performance_data()

    async def _cleanup_performance_data(self):
        """Clean up performance test data."""
        pass

    def measure_execution_time(self, func, *args, **kwargs) -> tuple[any, float]:
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    async def measure_async_execution_time(
        self, func, *args, **kwargs
    ) -> tuple[any, float]:
        """Measure execution time of an async function."""
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    def get_memory_usage(self) -> dict[str, float]:
        """Get current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        }

    def get_cpu_usage(self) -> float:
        """Get current CPU usage."""
        return psutil.cpu_percent(interval=0.1)

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_authentication_performance(self, setup_performance_services):
        """Test authentication performance."""

        # Test user creation performance
        user_data = {
            "username": "perf_auth_user",
            "email": "perf_auth@example.com",
            "password": "password123",
            "full_name": "Performance Auth User",
            "is_active": True,
            "is_admin": False,
        }

        start_memory = self.get_memory_usage()
        start_cpu = self.get_cpu_usage()

        user, creation_time = await self.measure_async_execution_time(
            self.auth_service.create_user, user_data
        )

        end_memory = self.get_memory_usage()
        end_cpu = self.get_cpu_usage()

        # Performance assertions
        assert creation_time < 1.0  # Should complete within 1 second
        assert (
            end_memory["rss_mb"] - start_memory["rss_mb"] < 50
        )  # Memory increase < 50MB
        assert end_cpu - start_cpu < 20  # CPU increase < 20%

        # Test token creation performance
        token_data = {"sub": user["username"], "permissions": user["permissions"]}

        token, token_time = await self.measure_async_execution_time(
            self.auth_service.create_access_token, token_data
        )

        assert token_time < 0.1  # Should complete within 100ms
        assert token is not None

        # Test token verification performance
        payload, verify_time = await self.measure_async_execution_time(
            self.auth_service.verify_token, token
        )

        assert verify_time < 0.1  # Should complete within 100ms
        assert payload["sub"] == user["username"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tool_registration_performance(self, setup_performance_services):
        """Test tool registration performance."""

        tool_data = {
            "name": "Performance Test Tool",
            "description": "Tool for performance testing",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [
                {"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}
            ],
            "tags": ["performance"],
            "category": "test",
        }

        start_memory = self.get_memory_usage()

        tool_id, registration_time = await self.measure_async_execution_time(
            self.tool_service.register_tool, tool_data, self.test_user["username"]
        )

        end_memory = self.get_memory_usage()

        assert registration_time < 2.0  # Should complete within 2 seconds
        assert (
            end_memory["rss_mb"] - start_memory["rss_mb"] < 100
        )  # Memory increase < 100MB
        assert tool_id is not None

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tool_search_performance(self, setup_performance_services):
        """Test tool search performance."""

        # Register multiple tools for search testing
        tools_data = []
        for i in range(10):
            tool_data = {
                "name": f"Search Performance Tool {i}",
                "description": f"Tool {i} for search performance testing",
                "version": "1.0.0",
                "author": "Test Author",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "endpoints": [
                    {
                        "url": f"http://localhost:8001/test{i}",
                        "method": "POST",
                        "timeout": 30,
                    }
                ],
                "tags": ["performance", "search"],
                "category": "test",
            }
            tools_data.append(tool_data)

        # Register all tools
        for tool_data in tools_data:
            await self.tool_service.register_tool(tool_data, self.test_user["username"])

        # Test search performance
        search_query = {
            "query": "performance",
            "filters": {"category": "test"},
            "limit": 10,
            "offset": 0,
        }

        start_memory = self.get_memory_usage()

        results, search_time = await self.measure_async_execution_time(
            self.search_service.search_tools, search_query
        )

        end_memory = self.get_memory_usage()

        assert search_time < 1.0  # Should complete within 1 second
        assert (
            end_memory["rss_mb"] - start_memory["rss_mb"] < 50
        )  # Memory increase < 50MB
        assert len(results["tools"]) >= 10  # Should find all tools

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_performance(self, setup_performance_services):
        """Test cache performance."""

        # Test cache set performance
        cache_key = "perf_test_key"
        cache_value = {"data": "test_value", "timestamp": time.time()}

        start_time = time.time()
        await self.cache.set(cache_key, cache_value, ttl=300)
        set_time = time.time() - start_time

        assert set_time < 0.01  # Should complete within 10ms

        # Test cache get performance
        start_time = time.time()
        retrieved_value = await self.cache.get(cache_key)
        get_time = time.time() - start_time

        assert get_time < 0.01  # Should complete within 10ms
        assert retrieved_value == cache_value

        # Test cache miss performance
        start_time = time.time()
        missing_value = await self.cache.get("non_existent_key")
        miss_time = time.time() - start_time

        assert miss_time < 0.01  # Should complete within 10ms
        assert missing_value is None

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_circuit_breaker_performance(self, setup_performance_services):
        """Test circuit breaker performance."""

        # Test successful operation performance
        async def successful_operation():
            return "success"

        start_time = time.time()
        result = await self.circuit_breaker.call(successful_operation)
        success_time = time.time() - start_time

        assert success_time < 0.1  # Should complete within 100ms
        assert result == "success"

        # Test failed operation performance
        async def failed_operation():
            raise Exception("Test failure")

        start_time = time.time()
        try:
            await self.circuit_breaker.call(failed_operation)
        except Exception:
            pass
        failure_time = time.time() - start_time

        assert failure_time < 0.1  # Should complete within 100ms

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self, setup_performance_services):
        """Test rate limiter performance."""

        # Test rate limiter check performance
        user_id = "perf_test_user"

        start_time = time.time()
        allowed = await self.rate_limiter.is_allowed(user_id, "test_endpoint")
        check_time = time.time() - start_time

        assert check_time < 0.01  # Should complete within 10ms
        assert allowed is True

        # Test multiple rapid requests
        start_time = time.time()
        results = []
        for _ in range(10):
            result = await self.rate_limiter.is_allowed(user_id, "test_endpoint")
            results.append(result)
        batch_time = time.time() - start_time

        assert batch_time < 0.1  # Should complete within 100ms
        assert all(results)  # All should be allowed initially


class TestLoadTesting:
    """Load testing scenarios."""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_user_registration(self, test_settings):
        """Test concurrent user registration performance."""

        auth_service = AuthService(settings=test_settings)

        async def register_user(user_id: int):
            user_data = {
                "username": f"concurrent_user_{user_id}",
                "email": f"concurrent_{user_id}@example.com",
                "password": "password123",
                "full_name": f"Concurrent User {user_id}",
                "is_active": True,
                "is_admin": False,
            }
            return await auth_service.create_user(user_data)

        # Register 10 users concurrently
        start_time = time.time()
        tasks = [register_user(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        assert len(results) == 10
        assert total_time < 5.0  # Should complete within 5 seconds
        assert all(result is not None for result in results)

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_tool_registration(self, test_settings):
        """Test concurrent tool registration performance."""

        tool_service = ToolService(settings=test_settings)

        async def register_tool(tool_id: int):
            tool_data = {
                "name": f"Concurrent Tool {tool_id}",
                "description": f"Tool {tool_id} for concurrent testing",
                "version": "1.0.0",
                "author": "Test Author",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "endpoints": [
                    {
                        "url": f"http://localhost:8001/test{tool_id}",
                        "method": "POST",
                        "timeout": 30,
                    }
                ],
                "tags": ["concurrent"],
                "category": "test",
            }
            return await tool_service.register_tool(tool_data, f"user_{tool_id}")

        # Register 20 tools concurrently
        start_time = time.time()
        tasks = [register_tool(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        assert len(results) == 20
        assert total_time < 10.0  # Should complete within 10 seconds
        assert all(result is not None for result in results)

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self, test_settings):
        """Test concurrent search operations performance."""

        search_service = SearchService(settings=test_settings)

        async def perform_search(search_id: int):
            search_query = {
                "query": f"search test {search_id}",
                "filters": {"category": "test"},
                "limit": 10,
                "offset": 0,
            }
            return await search_service.search_tools(search_query)

        # Perform 50 searches concurrently
        start_time = time.time()
        tasks = [perform_search(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        assert len(results) == 50
        assert total_time < 5.0  # Should complete within 5 seconds
        assert all(result is not None for result in results)


class TestStressTesting:
    """Stress testing scenarios."""

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, test_settings):
        """Test memory usage under sustained load."""

        auth_service = AuthService(settings=test_settings)
        tool_service = ToolService(settings=test_settings)

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Create sustained load
        for i in range(100):
            # Create user
            user_data = {
                "username": f"stress_user_{i}",
                "email": f"stress_{i}@example.com",
                "password": "password123",
                "full_name": f"Stress User {i}",
                "is_active": True,
                "is_admin": False,
            }
            user = await auth_service.create_user(user_data)

            # Register tool
            tool_data = {
                "name": f"Stress Tool {i}",
                "description": f"Tool {i} for stress testing",
                "version": "1.0.0",
                "author": "Test Author",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
                "endpoints": [
                    {
                        "url": f"http://localhost:8001/stress{i}",
                        "method": "POST",
                        "timeout": 30,
                    }
                ],
                "tags": ["stress"],
                "category": "test",
            }
            await tool_service.register_tool(tool_data, user["username"])

            # Check memory every 10 operations
            if i % 10 == 0:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                assert memory_increase < 500  # Memory increase < 500MB

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory

        assert total_memory_increase < 1000  # Total memory increase < 1GB

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_cpu_usage_under_load(self, test_settings):
        """Test CPU usage under sustained load."""

        auth_service = AuthService(settings=test_settings)

        # Monitor CPU usage during sustained operations
        cpu_samples = []

        for i in range(50):
            start_cpu = psutil.cpu_percent(interval=0.1)

            # Perform multiple operations
            for j in range(10):
                user_data = {
                    "username": f"cpu_user_{i}_{j}",
                    "email": f"cpu_{i}_{j}@example.com",
                    "password": "password123",
                    "full_name": f"CPU User {i}_{j}",
                    "is_active": True,
                    "is_admin": False,
                }
                await auth_service.create_user(user_data)

            end_cpu = psutil.cpu_percent(interval=0.1)
            cpu_samples.append(end_cpu - start_cpu)

            # Check that CPU usage doesn't spike too high
            assert end_cpu < 90  # CPU usage < 90%

        # Check average CPU increase
        avg_cpu_increase = statistics.mean(cpu_samples)
        assert avg_cpu_increase < 30  # Average CPU increase < 30%


class TestPerformanceRegression:
    """Performance regression detection tests."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_authentication_benchmark(self, test_settings):
        """Benchmark authentication operations."""

        auth_service = AuthService(settings=test_settings)

        # Benchmark user creation
        user_data = {
            "username": "benchmark_user",
            "email": "benchmark@example.com",
            "password": "password123",
            "full_name": "Benchmark User",
            "is_active": True,
            "is_admin": False,
        }

        user, creation_time = await self.measure_async_execution_time(
            auth_service.create_user, user_data
        )

        # Store benchmark results for comparison
        benchmark_data = {
            "operation": "user_creation",
            "execution_time": creation_time,
            "timestamp": time.time(),
            "threshold": 1.0,  # 1 second threshold
        }

        assert creation_time < benchmark_data["threshold"]

        # Benchmark token creation
        token_data = {"sub": user["username"], "permissions": user["permissions"]}
        token, token_time = await self.measure_async_execution_time(
            auth_service.create_access_token, token_data
        )

        token_benchmark = {
            "operation": "token_creation",
            "execution_time": token_time,
            "timestamp": time.time(),
            "threshold": 0.1,  # 100ms threshold
        }

        assert token_time < token_benchmark["threshold"]

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_tool_operations_benchmark(self, test_settings):
        """Benchmark tool operations."""

        tool_service = ToolService(settings=test_settings)

        # Benchmark tool registration
        tool_data = {
            "name": "Benchmark Tool",
            "description": "Tool for benchmarking",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object", "properties": {}},
            "endpoints": [
                {
                    "url": "http://localhost:8001/benchmark",
                    "method": "POST",
                    "timeout": 30,
                }
            ],
            "tags": ["benchmark"],
            "category": "test",
        }

        tool_id, registration_time = await self.measure_async_execution_time(
            tool_service.register_tool, tool_data, "benchmark_user"
        )

        registration_benchmark = {
            "operation": "tool_registration",
            "execution_time": registration_time,
            "timestamp": time.time(),
            "threshold": 2.0,  # 2 second threshold
        }

        assert registration_time < registration_benchmark["threshold"]

        # Benchmark tool retrieval
        tool, retrieval_time = await self.measure_async_execution_time(
            tool_service.get_tool, tool_id, "benchmark_user"
        )

        retrieval_benchmark = {
            "operation": "tool_retrieval",
            "execution_time": retrieval_time,
            "timestamp": time.time(),
            "threshold": 0.5,  # 500ms threshold
        }

        assert retrieval_time < retrieval_benchmark["threshold"]


class TestResourceMonitoring:
    """Resource monitoring tests."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, test_settings):
        """Test for memory leaks during operations."""

        auth_service = AuthService(settings=test_settings)

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Perform operations that should not leak memory
        for i in range(20):
            user_data = {
                "username": f"leak_test_user_{i}",
                "email": f"leak_test_{i}@example.com",
                "password": "password123",
                "full_name": f"Leak Test User {i}",
                "is_active": True,
                "is_admin": False,
            }
            user = await auth_service.create_user(user_data)

            # Create and verify token
            token_data = {"sub": user["username"], "permissions": user["permissions"]}
            token = await auth_service.create_access_token(token_data)
            await auth_service.verify_token(token)

        # Force garbage collection
        import gc

        gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (not a leak)
        assert memory_increase < 200  # Memory increase < 200MB

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cpu_efficiency(self, test_settings):
        """Test CPU efficiency during operations."""

        auth_service = AuthService(settings=test_settings)

        # Monitor CPU usage during operations
        cpu_samples = []

        for i in range(10):
            start_cpu = psutil.cpu_percent(interval=0.1)

            # Perform authentication operations
            user_data = {
                "username": f"cpu_efficiency_user_{i}",
                "email": f"cpu_efficiency_{i}@example.com",
                "password": "password123",
                "full_name": f"CPU Efficiency User {i}",
                "is_active": True,
                "is_admin": False,
            }
            user = await auth_service.create_user(user_data)

            token_data = {"sub": user["username"], "permissions": user["permissions"]}
            token = await auth_service.create_access_token(token_data)
            await auth_service.verify_token(token)

            end_cpu = psutil.cpu_percent(interval=0.1)
            cpu_samples.append(end_cpu - start_cpu)

        # Check CPU efficiency
        avg_cpu_usage = statistics.mean(cpu_samples)
        max_cpu_usage = max(cpu_samples)

        assert avg_cpu_usage < 20  # Average CPU usage < 20%
        assert max_cpu_usage < 50  # Peak CPU usage < 50%
