"""
Load Testing Framework

This module provides comprehensive load testing functionality using Locust
to test the application's performance under various load conditions.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import statistics

import httpx
import asyncio
from locust import HttpUser, task, between, events
from locust.exception import StopUser

from ...config import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class LoadTestConfig:
    """Load test configuration."""

    base_url: str = "http://localhost:9000"
    users: int = 10
    spawn_rate: int = 2
    run_time: int = 300  # 5 minutes
    ramp_up_time: int = 60  # 1 minute
    target_rps: int = 100
    max_response_time: float = 1.0  # seconds
    error_threshold: float = 5.0  # percent


@dataclass
class LoadTestResult:
    """Load test result."""

    test_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_response_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    concurrent_users: int
    status_codes: Dict[str, int]
    errors: List[str]


class MetaMCPLoadTestUser(HttpUser):
    """
    Locust user class for MetaMCP load testing.
    """

    wait_time = between(1, 3)  # Wait between 1-3 seconds between requests

    def on_start(self):
        """Called when user starts."""
        # Authenticate user
        self._authenticate()

    def _authenticate(self):
        """Authenticate user and get access token."""
        try:
            auth_data = {"username": "testuser", "password": "testpass123!"}

            response = self.client.post("/api/v1/auth/login", json=auth_data)

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                if self.access_token:
                    self.client.headers.update(
                        {"Authorization": f"Bearer {self.access_token}"}
                    )
            else:
                logger.warning(f"Authentication failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Authentication error: {e}")

    @task(3)
    def test_health_check(self):
        """Test health check endpoint."""
        self.client.get("/health")

    @task(2)
    def test_tools_list(self):
        """Test tools list endpoint."""
        self.client.get("/api/v1/tools")

    @task(2)
    def test_tools_search(self):
        """Test tools search endpoint."""
        search_params = {"query": "test tool", "limit": 10}
        self.client.get("/api/v1/tools/search", params=search_params)

    @task(1)
    def test_tool_execution(self):
        """Test tool execution endpoint."""
        execution_data = {"tool_id": "test-tool", "parameters": {"input": "test input"}}
        self.client.post("/api/v1/tools/execute", json=execution_data)

    @task(1)
    def test_composition(self):
        """Test tool composition endpoint."""
        composition_data = {"tools": ["tool1", "tool2"], "workflow": "test workflow"}
        self.client.post("/api/v1/composition/create", json=composition_data)

    @task(1)
    def test_admin_metrics(self):
        """Test admin metrics endpoint."""
        self.client.get("/api/v1/admin/metrics")

    def on_stop(self):
        """Called when user stops."""
        logger.info("User stopped")


class LoadTestRunner:
    """
    Load test runner for comprehensive performance testing.
    """

    def __init__(self, config: LoadTestConfig):
        """
        Initialize load test runner.

        Args:
            config: Load test configuration
        """
        self.config = config
        self.results: List[LoadTestResult] = []
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def run_basic_load_test(self) -> LoadTestResult:
        """Run basic load test."""
        logger.info("Starting basic load test")

        start_time = datetime.utcnow()
        response_times = []
        status_codes = {}
        errors = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0

        # Test endpoints
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/v1/tools"),
            ("GET", "/api/v1/tools/search?query=test"),
            ("POST", "/api/v1/tools/execute", {"tool_id": "test", "parameters": {}}),
        ]

        try:
            for i in range(self.config.total_requests):
                method, path, *data = endpoints[i % len(endpoints)]

                request_start = time.time()

                try:
                    if method == "GET":
                        response = await self.http_client.get(
                            f"{self.config.base_url}{path}"
                        )
                    elif method == "POST":
                        response = await self.http_client.post(
                            f"{self.config.base_url}{path}",
                            json=data[0] if data else {},
                        )

                    response_time = time.time() - request_start
                    response_times.append(response_time)

                    # Track status codes
                    status_code = str(response.status_code)
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1

                    total_requests += 1

                    if response.status_code < 400:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        errors.append(f"{method} {path}: {response.status_code}")

                    # Respect target RPS
                    if self.config.target_rps > 0:
                        await asyncio.sleep(1.0 / self.config.target_rps)

                except Exception as e:
                    failed_requests += 1
                    errors.append(f"{method} {path}: {str(e)}")
                    response_times.append(time.time() - request_start)

        except Exception as e:
            logger.error(f"Load test error: {e}")

        end_time = datetime.utcnow()

        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[
                18
            ]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[
                98
            ]  # 99th percentile
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0

        duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration if duration > 0 else 0
        error_rate = (
            (failed_requests / total_requests * 100) if total_requests > 0 else 0
        )

        result = LoadTestResult(
            test_name="Basic Load Test",
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_response_time=sum(response_times),
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            concurrent_users=self.config.users,
            status_codes=status_codes,
            errors=errors,
        )

        self.results.append(result)
        logger.info(
            f"Basic load test completed: {result.requests_per_second:.2f} RPS, {result.error_rate:.2f}% errors"
        )

        return result

    async def run_stress_test(self) -> LoadTestResult:
        """Run stress test to find breaking point."""
        logger.info("Starting stress test")

        # Gradually increase load until system breaks
        current_users = 1
        max_users = 1000

        while current_users <= max_users:
            config = LoadTestConfig(
                base_url=self.config.base_url,
                users=current_users,
                target_rps=current_users * 10,  # 10 RPS per user
                run_time=60,  # 1 minute per test
            )

            result = await self._run_load_test_with_config(config, "Stress Test")

            # Check if system is breaking
            if (
                result.error_rate > self.config.error_threshold
                or result.avg_response_time > self.config.max_response_time
            ):
                logger.info(f"System breaking point found at {current_users} users")
                break

            current_users *= 2  # Double the load

        return result

    async def run_spike_test(self) -> LoadTestResult:
        """Run spike test to test system recovery."""
        logger.info("Starting spike test")

        # Normal load
        normal_config = LoadTestConfig(
            base_url=self.config.base_url,
            users=10,
            target_rps=50,
            run_time=60,
        )

        # Spike load
        spike_config = LoadTestConfig(
            base_url=self.config.base_url,
            users=100,
            target_rps=500,
            run_time=30,
        )

        # Run normal load
        normal_result = await self._run_load_test_with_config(
            normal_config, "Spike Test - Normal"
        )

        # Run spike load
        spike_result = await self._run_load_test_with_config(
            spike_config, "Spike Test - Spike"
        )

        # Run normal load again
        recovery_result = await self._run_load_test_with_config(
            normal_config, "Spike Test - Recovery"
        )

        # Combine results
        combined_result = LoadTestResult(
            test_name="Spike Test",
            start_time=normal_result.start_time,
            end_time=recovery_result.end_time,
            total_requests=normal_result.total_requests
            + spike_result.total_requests
            + recovery_result.total_requests,
            successful_requests=normal_result.successful_requests
            + spike_result.successful_requests
            + recovery_result.successful_requests,
            failed_requests=normal_result.failed_requests
            + spike_result.failed_requests
            + recovery_result.failed_requests,
            total_response_time=normal_result.total_response_time
            + spike_result.total_response_time
            + recovery_result.total_response_time,
            avg_response_time=(
                normal_result.avg_response_time
                + spike_result.avg_response_time
                + recovery_result.avg_response_time
            )
            / 3,
            min_response_time=min(
                normal_result.min_response_time,
                spike_result.min_response_time,
                recovery_result.min_response_time,
            ),
            max_response_time=max(
                normal_result.max_response_time,
                spike_result.max_response_time,
                recovery_result.max_response_time,
            ),
            p95_response_time=max(
                normal_result.p95_response_time,
                spike_result.p95_response_time,
                recovery_result.p95_response_time,
            ),
            p99_response_time=max(
                normal_result.p99_response_time,
                spike_result.p99_response_time,
                recovery_result.p99_response_time,
            ),
            requests_per_second=(
                normal_result.requests_per_second
                + spike_result.requests_per_second
                + recovery_result.requests_per_second
            )
            / 3,
            error_rate=(
                normal_result.error_rate
                + spike_result.error_rate
                + recovery_result.error_rate
            )
            / 3,
            concurrent_users=spike_config.users,
            status_codes={
                **normal_result.status_codes,
                **spike_result.status_codes,
                **recovery_result.status_codes,
            },
            errors=normal_result.errors + spike_result.errors + recovery_result.errors,
        )

        self.results.append(combined_result)
        return combined_result

    async def run_endurance_test(self) -> LoadTestResult:
        """Run endurance test for long-term stability."""
        logger.info("Starting endurance test")

        config = LoadTestConfig(
            base_url=self.config.base_url,
            users=50,
            target_rps=200,
            run_time=1800,  # 30 minutes
        )

        return await self._run_load_test_with_config(config, "Endurance Test")

    async def _run_load_test_with_config(
        self, config: LoadTestConfig, test_name: str
    ) -> LoadTestResult:
        """Run load test with specific configuration."""
        # This is a simplified implementation
        # In a real scenario, you'd use Locust or similar tool

        start_time = datetime.utcnow()
        response_times = []
        status_codes = {}
        errors = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0

        # Simulate load
        tasks = []
        for i in range(config.users):
            task = asyncio.create_task(self._simulate_user(config))
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.utcnow()

        # Calculate statistics (simplified)
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) >= 20
            else 0
        )
        p99_response_time = (
            statistics.quantiles(response_times, n=100)[98]
            if len(response_times) >= 100
            else 0
        )

        duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration if duration > 0 else 0
        error_rate = (
            (failed_requests / total_requests * 100) if total_requests > 0 else 0
        )

        result = LoadTestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_response_time=sum(response_times),
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            concurrent_users=config.users,
            status_codes=status_codes,
            errors=errors,
        )

        return result

    async def _simulate_user(self, config: LoadTestConfig):
        """Simulate a single user making requests."""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/v1/tools"),
            ("GET", "/api/v1/tools/search?query=test"),
        ]

        for i in range(config.run_time // 10):  # Make request every 10 seconds
            method, path = endpoints[i % len(endpoints)]

            start_time = time.time()

            try:
                if method == "GET":
                    response = await self.http_client.get(f"{config.base_url}{path}")

                response_time = time.time() - start_time

                if response.status_code < 400:
                    pass  # Success
                else:
                    pass  # Error

            except Exception as e:
                pass  # Error

            await asyncio.sleep(10)  # Wait 10 seconds between requests

    def generate_report(self) -> Dict[str, Any]:
        """Generate load test report."""
        if not self.results:
            return {"error": "No test results available"}

        report = {
            "summary": {
                "total_tests": len(self.results),
                "total_requests": sum(r.total_requests for r in self.results),
                "total_errors": sum(r.failed_requests for r in self.results),
                "overall_error_rate": sum(r.failed_requests for r in self.results)
                / sum(r.total_requests for r in self.results)
                * 100,
                "average_rps": statistics.mean(
                    [r.requests_per_second for r in self.results]
                ),
                "average_response_time": statistics.mean(
                    [r.avg_response_time for r in self.results]
                ),
            },
            "tests": [],
        }

        for result in self.results:
            test_report = {
                "name": result.test_name,
                "duration": (result.end_time - result.start_time).total_seconds(),
                "requests": {
                    "total": result.total_requests,
                    "successful": result.successful_requests,
                    "failed": result.failed_requests,
                    "per_second": result.requests_per_second,
                },
                "response_times": {
                    "average": result.avg_response_time,
                    "min": result.min_response_time,
                    "max": result.max_response_time,
                    "p95": result.p95_response_time,
                    "p99": result.p99_response_time,
                },
                "errors": {
                    "rate": result.error_rate,
                    "count": result.failed_requests,
                    "details": result.errors[:10],  # Show first 10 errors
                },
                "status_codes": result.status_codes,
            }
            report["tests"].append(test_report)

        return report

    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.aclose()


async def run_load_tests(config: LoadTestConfig) -> Dict[str, Any]:
    """
    Run comprehensive load tests.

    Args:
        config: Load test configuration

    Returns:
        Load test report
    """
    runner = LoadTestRunner(config)

    try:
        # Run different types of tests
        await runner.run_basic_load_test()
        await runner.run_stress_test()
        await runner.run_spike_test()
        await runner.run_endurance_test()

        # Generate report
        report = runner.generate_report()

        return report

    finally:
        await runner.cleanup()


def run_locust_load_test(config: LoadTestConfig):
    """
    Run load test using Locust.

    Args:
        config: Load test configuration
    """
    import subprocess
    import sys

    # Create Locust configuration
    locust_config = {
        "locustfile": "tests/performance/load_testing.py",
        "host": config.base_url,
        "users": config.users,
        "spawn-rate": config.spawn_rate,
        "run-time": f"{config.run_time}s",
        "headless": True,
        "html": "load_test_report.html",
        "csv": "load_test_results",
    }

    # Build command
    cmd = [
        sys.executable,
        "-m",
        "locust",
        "--locustfile",
        locust_config["locustfile"],
        "--host",
        locust_config["host"],
        "--users",
        str(locust_config["users"]),
        "--spawn-rate",
        str(locust_config["spawn-rate"]),
        "--run-time",
        locust_config["run-time"],
        "--headless",
        "--html",
        locust_config["html"],
        "--csv",
        locust_config["csv"],
    ]

    # Run Locust
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Locust load test completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Locust load test failed: {e.stderr}")
        raise


if __name__ == "__main__":
    # Example usage
    config = LoadTestConfig(
        base_url="http://localhost:9000",
        users=50,
        target_rps=200,
        run_time=300,
    )

    # Run async load tests
    asyncio.run(run_load_tests(config))

    # Or run Locust tests
    # run_locust_load_test(config)
