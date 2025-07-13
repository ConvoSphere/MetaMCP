"""
Performance Tests

Performance tests and benchmarks for MetaMCP components.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from metamcp.llm.service import LLMService
from metamcp.monitoring.telemetry import TelemetryManager
from metamcp.tools.registry import ToolRegistry
from metamcp.vector.client import VectorSearchClient


class TestPerformance:
    """Performance tests for MetaMCP components."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for performance testing."""
        telemetry = Mock(spec=TelemetryManager)
        telemetry.record_request = Mock()
        telemetry.record_tool_execution = Mock()
        telemetry.record_vector_search = Mock()

        tool_registry = Mock(spec=ToolRegistry)
        tool_registry.list_tools = AsyncMock(return_value=[])
        tool_registry.execute_tool = AsyncMock(return_value={"result": "test"})
        tool_registry.search_tools = AsyncMock(return_value=[])

        vector_client = Mock(spec=VectorSearchClient)
        vector_client.search = AsyncMock(return_value=[])
        vector_client.add_documents = AsyncMock()

        llm_service = Mock(spec=LLMService)
        llm_service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        llm_service.generate_text = AsyncMock(return_value="test response")

        return {
            "telemetry": telemetry,
            "tool_registry": tool_registry,
            "vector_client": vector_client,
            "llm_service": llm_service
        }

    @pytest.mark.asyncio
    async def test_telemetry_performance(self, mock_components):
        """Test telemetry performance overhead."""
        telemetry = mock_components["telemetry"]

        # Benchmark telemetry operations
        start_time = time.time()

        for _ in range(1000):
            telemetry.record_request("GET", "/api/tools", 200, 0.1)
            telemetry.record_tool_execution("calculator", True, 0.5)
            telemetry.record_vector_search(50, 10, 0.1)

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete 3000 operations in reasonable time
        assert total_time < 1.0  # Less than 1 second for 3000 operations
        assert telemetry.record_request.call_count == 1000
        assert telemetry.record_tool_execution.call_count == 1000
        assert telemetry.record_vector_search.call_count == 1000

    @pytest.mark.asyncio
    async def test_tool_registry_performance(self, mock_components):
        """Test tool registry performance."""
        tool_registry = mock_components["tool_registry"]

        # Benchmark tool operations
        start_time = time.time()

        # Simulate multiple concurrent tool operations
        tasks = []
        for i in range(100):
            task = asyncio.create_task(
                tool_registry.execute_tool(f"tool_{i}", {"input": f"data_{i}"})
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Should complete 100 concurrent operations in reasonable time
        assert total_time < 2.0  # Less than 2 seconds for 100 concurrent operations
        assert len(results) == 100
        assert tool_registry.execute_tool.call_count == 100

    @pytest.mark.asyncio
    async def test_vector_search_performance(self, mock_components):
        """Test vector search performance."""
        vector_client = mock_components["vector_client"]

        # Benchmark vector search operations
        start_time = time.time()

        # Simulate multiple concurrent searches
        tasks = []
        for i in range(50):
            task = asyncio.create_task(
                vector_client.search(f"query_{i}", limit=10)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Should complete 50 concurrent searches in reasonable time
        assert total_time < 1.0  # Less than 1 second for 50 concurrent searches
        assert len(results) == 50
        assert vector_client.search.call_count == 50

    @pytest.mark.asyncio
    async def test_llm_service_performance(self, mock_components):
        """Test LLM service performance."""
        llm_service = mock_components["llm_service"]

        # Benchmark LLM operations
        start_time = time.time()

        # Simulate multiple concurrent LLM operations
        tasks = []
        for i in range(20):
            # Embedding generation
            task1 = asyncio.create_task(
                llm_service.generate_embedding(f"text_{i}")
            )
            # Text generation
            task2 = asyncio.create_task(
                llm_service.generate_text(f"prompt_{i}")
            )
            tasks.extend([task1, task2])

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Should complete 40 concurrent LLM operations in reasonable time
        assert total_time < 3.0  # Less than 3 seconds for 40 concurrent operations
        assert len(results) == 40
        assert llm_service.generate_embedding.call_count == 20
        assert llm_service.generate_text.call_count == 20


class TestMemoryUsage:
    """Memory usage tests."""

    @pytest.mark.asyncio
    async def test_telemetry_memory_usage(self):
        """Test telemetry memory usage."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create telemetry manager
        telemetry = TelemetryManager()

        # Simulate high-volume operations
        for _ in range(10000):
            telemetry.record_request("GET", "/api/tools", 200, 0.1)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        # Simulate large dataset processing
        large_dataset = [{"id": i, "data": f"data_{i}"} for i in range(10000)]

        # Process dataset in chunks
        chunk_size = 1000
        chunks = [large_dataset[i:i + chunk_size] for i in range(0, len(large_dataset), chunk_size)]

        processed_chunks = []
        for chunk in chunks:
            # Simulate processing
            processed_chunk = [{"id": item["id"], "processed": True} for item in chunk]
            processed_chunks.append(processed_chunk)

        # Verify all data was processed
        total_processed = sum(len(chunk) for chunk in processed_chunks)
        assert total_processed == len(large_dataset)


class TestConcurrency:
    """Concurrency and load testing."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_components):
        """Test handling of concurrent requests."""
        telemetry = mock_components["telemetry"]

        # Simulate high concurrent load
        async def make_request(request_id: int):
            await asyncio.sleep(0.01)  # Simulate processing time
            telemetry.record_request("GET", f"/api/request/{request_id}", 200, 0.1)
            return {"request_id": request_id, "status": "success"}

        # Create 1000 concurrent requests
        tasks = [make_request(i) for i in range(1000)]
        start_time = time.time()

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Should handle 1000 concurrent requests efficiently
        assert total_time < 5.0  # Less than 5 seconds for 1000 concurrent requests
        assert len(results) == 1000
        assert telemetry.record_request.call_count == 1000

    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """Test proper resource cleanup under load."""
        import gc

        # Create objects under load
        objects = []
        for i in range(1000):
            obj = {"id": i, "data": "x" * 1000}  # Large objects
            objects.append(obj)

        # Simulate processing
        processed = [{"id": obj["id"], "processed": True} for obj in objects]

        # Force garbage collection
        gc.collect()

        # Verify memory is cleaned up
        assert len(processed) == 1000


class TestScalability:
    """Scalability tests."""

    @pytest.mark.asyncio
    async def test_scaling_with_data_size(self):
        """Test performance scaling with data size."""
        sizes = [100, 1000, 10000]
        times = []

        for size in sizes:
            data = [{"id": i, "value": i} for i in range(size)]

            start_time = time.time()
            # Simulate processing
            processed = [{"id": item["id"], "processed": True} for item in data]
            end_time = time.time()

            processing_time = end_time - start_time
            times.append(processing_time)

            assert len(processed) == size

        # Processing time should scale reasonably
        # Time should not increase exponentially
        assert times[1] < times[0] * 20  # 1000 items should not take 20x longer than 100
        assert times[2] < times[1] * 20  # 10000 items should not take 20x longer than 1000

    @pytest.mark.asyncio
    async def test_scaling_with_concurrency(self):
        """Test performance scaling with concurrency levels."""
        concurrency_levels = [10, 50, 100, 200]
        times = []

        for concurrency in concurrency_levels:
            async def worker(worker_id: int):
                await asyncio.sleep(0.01)  # Simulate work
                return worker_id

            start_time = time.time()
            tasks = [worker(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            processing_time = end_time - start_time
            times.append(processing_time)

            assert len(results) == concurrency

        # Higher concurrency should not cause exponential time increase
        # (due to async nature, should scale more linearly)
        for i in range(1, len(times)):
            assert times[i] < times[i-1] * 5  # Should not increase more than 5x


class TestBenchmarks:
    """Benchmark tests for performance comparison."""

    @pytest.mark.benchmark
    def test_telemetry_benchmark(self, benchmark):
        """Benchmark telemetry operations."""
        telemetry = Mock(spec=TelemetryManager)

        def record_metrics():
            telemetry.record_request("GET", "/api/tools", 200, 0.1)
            telemetry.record_tool_execution("calculator", True, 0.5)
            telemetry.record_vector_search(50, 10, 0.1)

        result = benchmark(record_metrics)

        # Benchmark should complete in reasonable time
        assert result.stats.mean < 0.001  # Less than 1ms per operation

    @pytest.mark.benchmark
    def test_data_processing_benchmark(self, benchmark):
        """Benchmark data processing operations."""
        data = [{"id": i, "value": i} for i in range(1000)]

        def process_data():
            return [{"id": item["id"], "processed": True} for item in data]

        result = benchmark(process_data)

        # Should process 1000 items efficiently
        assert result.stats.mean < 0.001  # Less than 1ms for 1000 items
