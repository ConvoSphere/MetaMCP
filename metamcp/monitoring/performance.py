"""
Performance Monitoring System

This module provides comprehensive performance monitoring including
metrics collection, profiling, and performance analysis.
"""

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary

from ..config import get_settings
from ..utils.constants import METRICS_UPDATE_INTERVAL
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_usage_percent: float
    disk_used: int
    disk_total: int
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    request_rate: float
    response_time_avg: float
    error_rate: float


@dataclass
class RequestMetrics:
    """Request-specific metrics."""

    method: str
    path: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_agent: str | None = None
    client_ip: str | None = None
    request_size: int | None = None
    response_size: int | None = None


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Provides system metrics, request tracking, and performance analysis.
    """

    def __init__(self) -> None:
        """Initialize performance monitor."""
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self.request_history: deque = deque(maxlen=10000)  # Keep last 10000 requests

        # System metrics
        self.last_cpu_percent = 0
        self.last_memory_percent = 0
        self.last_network_io = psutil.net_io_counters()
        self.last_network_time = time.time()

        # Request tracking
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
        self.request_times: deque = deque(maxlen=1000)

        # Performance thresholds
        self.cpu_threshold = 80.0  # CPU usage threshold
        self.memory_threshold = 85.0  # Memory usage threshold
        self.response_time_threshold = 1.0  # Response time threshold (seconds)
        self.error_rate_threshold = 5.0  # Error rate threshold (percent)

        # Prometheus metrics
        self._setup_prometheus_metrics()

        # Monitoring state
        self._monitoring_task: asyncio.Task | None = None
        self._running = False

        logger.info("Performance monitor initialized")

    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics."""
        # System metrics
        self.cpu_gauge = Gauge(
            "metamcp_cpu_usage_percent", "CPU usage percentage", ["component"]
        )
        self.memory_gauge = Gauge(
            "metamcp_memory_usage_bytes", "Memory usage in bytes", ["component"]
        )
        self.memory_percent_gauge = Gauge(
            "metamcp_memory_usage_percent", "Memory usage percentage", ["component"]
        )
        self.disk_gauge = Gauge(
            "metamcp_disk_usage_bytes", "Disk usage in bytes", ["component"]
        )
        self.disk_percent_gauge = Gauge(
            "metamcp_disk_usage_percent", "Disk usage percentage", ["component"]
        )

        # Network metrics
        self.network_bytes_sent = Counter(
            "metamcp_network_bytes_sent_total", "Total bytes sent", ["component"]
        )
        self.network_bytes_recv = Counter(
            "metamcp_network_bytes_recv_total", "Total bytes received", ["component"]
        )

        # Request metrics
        self.request_counter = Counter(
            "metamcp_requests_total",
            "Total requests",
            ["method", "path", "status_code"],
        )
        self.request_duration = Histogram(
            "metamcp_request_duration_seconds",
            "Request duration in seconds",
            ["method", "path"],
        )
        self.active_requests = Gauge(
            "metamcp_active_requests", "Number of active requests"
        )

        # Error metrics
        self.error_counter = Counter(
            "metamcp_errors_total", "Total errors", ["error_type", "component"]
        )
        self.error_rate = Gauge("metamcp_error_rate_percent", "Error rate percentage")

        # Performance metrics
        self.response_time_summary = Summary(
            "metamcp_response_time_seconds", "Response time summary", ["method", "path"]
        )
        self.request_rate = Gauge(
            "metamcp_request_rate_per_second", "Requests per second"
        )

    async def start(self) -> None:
        """Start performance monitoring."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")

    async def stop(self) -> None:
        """Stop performance monitoring."""
        if not self._running:
            return

        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._collect_system_metrics()
                await self._update_prometheus_metrics()
                await asyncio.sleep(METRICS_UPDATE_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total

            # Network usage
            network_io = psutil.net_io_counters()
            current_time = time.time()
            time_diff = current_time - self.last_network_time

            network_bytes_sent = network_io.bytes_sent
            network_bytes_recv = network_io.bytes_recv

            # Calculate network rates
            if time_diff > 0:
                sent_rate = (
                    network_bytes_sent - self.last_network_io.bytes_sent
                ) / time_diff
                recv_rate = (
                    network_bytes_recv - self.last_network_io.bytes_recv
                ) / time_diff
            else:
                sent_rate = 0
                recv_rate = 0

            # Update last values
            self.last_network_io = network_io
            self.last_network_time = current_time

            # Calculate request metrics
            request_rate = self._calculate_request_rate()
            response_time_avg = self._calculate_average_response_time()
            error_rate = self._calculate_error_rate()

            # Create metrics object
            metrics = PerformanceMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used=memory_used,
                memory_total=memory_total,
                disk_usage_percent=disk_usage_percent,
                disk_used=disk_used,
                disk_total=disk_total,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                active_connections=self._get_active_connections(),
                request_rate=request_rate,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
            )

            # Store metrics
            self.metrics_history.append(metrics)

            # Check thresholds
            await self._check_performance_thresholds(metrics)

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _update_prometheus_metrics(self) -> None:
        """Update Prometheus metrics."""
        try:
            if not self.metrics_history:
                return

            latest_metrics = self.metrics_history[-1]

            # Update system metrics
            self.cpu_gauge.labels(component="system").set(latest_metrics.cpu_percent)
            self.memory_gauge.labels(component="system").set(latest_metrics.memory_used)
            self.memory_percent_gauge.labels(component="system").set(
                latest_metrics.memory_percent
            )
            self.disk_gauge.labels(component="system").set(latest_metrics.disk_used)
            self.disk_percent_gauge.labels(component="system").set(
                latest_metrics.disk_usage_percent
            )

            # Update network metrics
            self.network_bytes_sent.labels(component="system").inc(
                latest_metrics.network_bytes_sent
            )
            self.network_bytes_recv.labels(component="system").inc(
                latest_metrics.network_bytes_recv
            )

            # Update performance metrics
            self.request_rate.set(latest_metrics.request_rate)
            self.error_rate.set(latest_metrics.error_rate)

        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")

    async def _check_performance_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check performance thresholds and log warnings."""
        warnings = []

        if metrics.cpu_percent > self.cpu_threshold:
            warnings.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        if metrics.memory_percent > self.memory_threshold:
            warnings.append(f"High memory usage: {metrics.memory_percent:.1f}%")

        if metrics.response_time_avg > self.response_time_threshold:
            warnings.append(f"High response time: {metrics.response_time_avg:.3f}s")

        if metrics.error_rate > self.error_rate_threshold:
            warnings.append(f"High error rate: {metrics.error_rate:.1f}%")

        if warnings:
            logger.warning(f"Performance warnings: {'; '.join(warnings)}")

    def record_request(self, request_metrics: RequestMetrics) -> None:
        """
        Record request metrics.

        Args:
            request_metrics: Request metrics to record
        """
        try:
            # Update counters
            self.request_count += 1
            self.total_response_time += request_metrics.response_time
            self.request_times.append(request_metrics.response_time)

            # Update Prometheus metrics
            self.request_counter.labels(
                method=request_metrics.method,
                path=request_metrics.path,
                status_code=str(request_metrics.status_code),
            ).inc()

            self.request_duration.labels(
                method=request_metrics.method, path=request_metrics.path
            ).observe(request_metrics.response_time)

            self.response_time_summary.labels(
                method=request_metrics.method, path=request_metrics.path
            ).observe(request_metrics.response_time)

            # Record error if status code indicates error
            if request_metrics.status_code >= 400:
                self.error_count += 1
                self.error_counter.labels(
                    error_type=f"http_{request_metrics.status_code}", component="api"
                ).inc()

            # Store in history
            self.request_history.append(request_metrics)

        except Exception as e:
            logger.error(f"Error recording request metrics: {e}")

    @contextmanager
    def track_request(self, method: str, path: str):
        """
        Context manager for tracking requests.

        Args:
            method: HTTP method
            path: Request path
        """
        start_time = time.time()
        self.active_requests.inc()

        try:
            yield
            status_code = 200  # Default success
        except Exception:
            status_code = 500  # Default error
            raise
        finally:
            response_time = time.time() - start_time
            self.active_requests.dec()

            # Record request metrics
            request_metrics = RequestMetrics(
                method=method,
                path=path,
                status_code=status_code,
                response_time=response_time,
                timestamp=datetime.utcnow(),
            )
            self.record_request(request_metrics)

    @asynccontextmanager
    async def track_request_async(self, method: str, path: str):
        """
        Async context manager for tracking requests.

        Args:
            method: HTTP method
            path: Request path
        """
        start_time = time.time()
        self.active_requests.inc()

        try:
            yield
            status_code = 200  # Default success
        except Exception:
            status_code = 500  # Default error
            raise
        finally:
            response_time = time.time() - start_time
            self.active_requests.dec()

            # Record request metrics
            request_metrics = RequestMetrics(
                method=method,
                path=path,
                status_code=status_code,
                response_time=response_time,
                timestamp=datetime.utcnow(),
            )
            self.record_request(request_metrics)

    def _calculate_request_rate(self) -> float:
        """Calculate requests per second."""
        if len(self.request_times) < 2:
            return 0.0

        # Calculate rate over last 60 seconds
        cutoff_time = time.time() - 60
        recent_requests = [
            req
            for req in self.request_history
            if req.timestamp.timestamp() > cutoff_time
        ]

        return float(len(recent_requests)) / 60.0

    def _calculate_average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.request_times:
            return 0.0

        return sum(self.request_times) / len(self.request_times)

    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.request_count == 0:
            return 0.0

        return (self.error_count / self.request_count) * 100.0

    def _get_active_connections(self) -> int:
        """Get number of active connections."""
        try:
            # This is a simplified implementation
            # In a real system, you'd track actual connections
            return len(self.request_history) if self.request_history else 0
        except Exception:
            return 0

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary."""
        if not self.metrics_history:
            return {}

        latest_metrics = self.metrics_history[-1]

        return {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "system": {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "memory_used_mb": latest_metrics.memory_used // (1024 * 1024),
                "memory_total_mb": latest_metrics.memory_total // (1024 * 1024),
                "disk_usage_percent": latest_metrics.disk_usage_percent,
                "disk_used_gb": latest_metrics.disk_used // (1024 * 1024 * 1024),
                "disk_total_gb": latest_metrics.disk_total // (1024 * 1024 * 1024),
            },
            "network": {
                "bytes_sent": latest_metrics.network_bytes_sent,
                "bytes_recv": latest_metrics.network_bytes_recv,
            },
            "requests": {
                "total_requests": self.request_count,
                "error_count": self.error_count,
                "request_rate": latest_metrics.request_rate,
                "response_time_avg": latest_metrics.response_time_avg,
                "error_rate": latest_metrics.error_rate,
                "active_connections": latest_metrics.active_connections,
            },
            "alerts": {
                "cpu_high": latest_metrics.cpu_percent > self.cpu_threshold,
                "memory_high": latest_metrics.memory_percent > self.memory_threshold,
                "response_time_high": latest_metrics.response_time_avg
                > self.response_time_threshold,
                "error_rate_high": latest_metrics.error_rate
                > self.error_rate_threshold,
            },
        }

    def get_request_analytics(self, hours: int = 24) -> dict[str, Any]:
        """Get request analytics for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Filter requests by time
        recent_requests = [
            req for req in self.request_history if req.timestamp > cutoff_time
        ]

        if not recent_requests:
            return {}

        # Calculate analytics
        total_requests = len(recent_requests)
        error_requests = len([r for r in recent_requests if r.status_code >= 400])

        # Group by path
        path_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
        for req in recent_requests:
            path_stats[req.path]["count"] += 1
            path_stats[req.path]["total_time"] += req.response_time
            if req.status_code >= 400:
                path_stats[req.path]["errors"] += 1

        # Calculate averages
        for path, stats in path_stats.items():
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["error_rate"] = (stats["errors"] / stats["count"]) * 100

        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate": (
                (error_requests / total_requests) * 100 if total_requests > 0 else 0
            ),
            "avg_response_time": sum(r.response_time for r in recent_requests)
            / total_requests,
            "path_statistics": dict(path_stats),
            "status_code_distribution": self._get_status_code_distribution(
                recent_requests
            ),
        }

    def _get_status_code_distribution(
        self, requests: list[RequestMetrics]
    ) -> dict[str, int]:
        """Get distribution of status codes."""
        distribution = defaultdict(int)
        for req in requests:
            status_range = f"{req.status_code // 100}xx"
            distribution[status_range] += 1
        return dict(distribution)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def track_performance(func: Callable) -> Callable:
    """
    Decorator to track function performance.

    Args:
        func: Function to track

    Returns:
        Decorated function
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Function {func.__name__} executed in {execution_time:.3f}s")

    return wrapper


async def track_performance_async(func: Callable) -> Callable:
    """
    Async decorator to track function performance.

    Args:
        func: Async function to track

    Returns:
        Decorated function
    """

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.debug(
                f"Async function {func.__name__} executed in {execution_time:.3f}s"
            )

    return wrapper
