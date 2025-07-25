"""
OpenTelemetry Telemetry Module

This module provides comprehensive observability using OpenTelemetry
for tracing, metrics, and logging across the MetaMCP application.
"""

from contextlib import asynccontextmanager
from typing import Any

# Try to import OpenTelemetry packages, but provide fallbacks if not available
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

    # Create dummy classes for fallback
    class DummyTracer:
        def start_span(self, name, attributes=None):
            return DummySpan()

    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key, value):
            pass

        def set_status(self, status):
            pass

    class DummyMeter:
        def create_counter(self, name, description=None, unit=None):
            return DummyCounter()

        def create_histogram(self, name, description=None, unit=None):
            return DummyHistogram()

    class DummyCounter:
        def add(self, value, attributes=None):
            pass

    class DummyHistogram:
        def record(self, value, attributes=None):
            pass


from ..config import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TelemetryManager:
    """
    OpenTelemetry Telemetry Manager.

    This class manages OpenTelemetry instrumentation for tracing,
    metrics, and logging across the MetaMCP application.
    """

    def __init__(self):
        """Initialize the telemetry manager."""
        self.settings = settings
        self.tracer_provider = None
        self.meter_provider = None
        self.tracer = None
        self.meter = None

        # Metric instruments
        self.request_counter = None
        self.request_duration = None
        self.tool_execution_counter = None
        self.tool_execution_duration = None
        self.vector_search_counter = None
        self.vector_search_duration = None

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize OpenTelemetry telemetry."""
        if self._initialized:
            return

        try:
            if not OPENTELEMETRY_AVAILABLE:
                logger.warning(
                    "OpenTelemetry packages not available, using fallback telemetry"
                )
                self._initialized = True
                return

            logger.info("Initializing OpenTelemetry Telemetry...")

            # Initialize tracing
            await self._initialize_tracing()

            # Initialize metrics
            await self._initialize_metrics()

            # Create instruments
            self._create_instruments()

            self._initialized = True
            logger.info("OpenTelemetry Telemetry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry Telemetry: {e}")
            # Fallback to dummy telemetry
            self._initialized = True

    async def _initialize_tracing(self) -> None:
        """Initialize OpenTelemetry tracing."""
        if not OPENTELEMETRY_AVAILABLE:
            self.tracer = DummyTracer()
            return

        try:
            # Create tracer provider
            self.tracer_provider = TracerProvider()

            # Configure span processor
            if self.settings.otlp_endpoint:
                # OTLP exporter for distributed tracing
                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.settings.otlp_endpoint,
                    insecure=self.settings.otlp_insecure,
                )
                span_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            # Create tracer
            self.tracer = trace.get_tracer("metamcp")

            logger.info("OpenTelemetry tracing initialized")

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            self.tracer = DummyTracer()

    async def _initialize_metrics(self) -> None:
        """Initialize OpenTelemetry metrics."""
        if not OPENTELEMETRY_AVAILABLE:
            self.meter = DummyMeter()
            return

        try:
            # Create metric readers
            metric_readers = []

            # Prometheus exporter for metrics
            prometheus_reader = PrometheusMetricReader()
            metric_readers.append(prometheus_reader)

            # OTLP exporter for metrics (if configured)
            if self.settings.otlp_endpoint:
                otlp_metric_exporter = OTLPMetricExporter(
                    endpoint=self.settings.otlp_endpoint,
                    insecure=self.settings.otlp_insecure,
                )
                otlp_reader = PeriodicExportingMetricReader(otlp_metric_exporter)
                metric_readers.append(otlp_reader)

            # Create meter provider
            self.meter_provider = MeterProvider(metric_readers=metric_readers)

            # Set global meter provider
            metrics.set_meter_provider(self.meter_provider)

            # Create meter
            self.meter = metrics.get_meter("metamcp")

            logger.info("OpenTelemetry metrics initialized")

        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")
            self.meter = DummyMeter()

    def _create_instruments(self) -> None:
        """Create metric instruments."""
        if not self.meter:
            return

        try:
            # Request metrics
            self.request_counter = self.meter.create_counter(
                name="metamcp_requests_total",
                description="Total number of requests",
                unit="1",
            )

            self.request_duration = self.meter.create_histogram(
                name="metamcp_request_duration_seconds",
                description="Request duration in seconds",
                unit="s",
            )

            # Tool execution metrics
            self.tool_execution_counter = self.meter.create_counter(
                name="metamcp_tool_executions_total",
                description="Total number of tool executions",
                unit="1",
            )

            self.tool_execution_duration = self.meter.create_histogram(
                name="metamcp_tool_execution_duration_seconds",
                description="Tool execution duration in seconds",
                unit="s",
            )

            # Vector search metrics
            self.vector_search_counter = self.meter.create_counter(
                name="metamcp_vector_searches_total",
                description="Total number of vector searches",
                unit="1",
            )

            self.vector_search_duration = self.meter.create_histogram(
                name="metamcp_vector_search_duration_seconds",
                description="Vector search duration in seconds",
                unit="s",
            )

            logger.info("Metric instruments created")

        except Exception as e:
            logger.error(f"Failed to create metric instruments: {e}")

    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI application."""
        try:
            if not self._initialized:
                logger.warning(
                    "Telemetry not initialized, skipping FastAPI instrumentation"
                )
                return

            if not OPENTELEMETRY_AVAILABLE:
                logger.warning(
                    "OpenTelemetry not available, skipping FastAPI instrumentation"
                )
                return

            # Instrument FastAPI
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=self.tracer_provider,
                meter_provider=self.meter_provider,
            )

            logger.info("FastAPI instrumented with OpenTelemetry")

        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")

    def instrument_httpx(self) -> None:
        """Instrument HTTPX client."""
        try:
            if not self._initialized or not OPENTELEMETRY_AVAILABLE:
                return

            # Instrument HTTPX
            HTTPXClientInstrumentor().instrument()

            logger.info("HTTPX instrumented with OpenTelemetry")

        except Exception as e:
            logger.error(f"Failed to instrument HTTPX: {e}")

    def instrument_sqlalchemy(self) -> None:
        """Instrument SQLAlchemy."""
        try:
            if not self._initialized or not OPENTELEMETRY_AVAILABLE:
                return

            # Instrument SQLAlchemy
            SQLAlchemyInstrumentor().instrument()

            logger.info("SQLAlchemy instrumented with OpenTelemetry")

        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}")

    def record_request(
        self, method: str, path: str, status_code: int, duration: float
    ) -> None:
        """Record request metrics."""
        try:
            if self.request_counter:
                self.request_counter.add(
                    1,
                    attributes={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                    },
                )

            if self.request_duration:
                self.request_duration.record(
                    duration,
                    attributes={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")

    def record_tool_execution(
        self, tool_name: str, success: bool, duration: float
    ) -> None:
        """Record tool execution metrics."""
        try:
            if self.tool_execution_counter:
                self.tool_execution_counter.add(
                    1, attributes={"tool_name": tool_name, "success": success}
                )

            if self.tool_execution_duration:
                self.tool_execution_duration.record(
                    duration, attributes={"tool_name": tool_name, "success": success}
                )

        except Exception as e:
            logger.error(f"Failed to record tool execution metrics: {e}")

    def record_vector_search(
        self, query_length: int, result_count: int, duration: float
    ) -> None:
        """Record vector search metrics."""
        try:
            if self.vector_search_counter:
                self.vector_search_counter.add(
                    1,
                    attributes={
                        "query_length": query_length,
                        "result_count": result_count,
                    },
                )

            if self.vector_search_duration:
                self.vector_search_duration.record(
                    duration,
                    attributes={
                        "query_length": query_length,
                        "result_count": result_count,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to record vector search metrics: {e}")

    @asynccontextmanager
    async def trace_operation(
        self, operation_name: str, attributes: dict[str, Any] | None = None
    ):
        """Context manager for tracing operations."""
        if not self.tracer:
            yield
            return

        try:
            with self.tracer.start_span(
                operation_name, attributes=attributes or {}
            ) as span:
                yield span
        except Exception as e:
            logger.error(f"Failed to trace operation {operation_name}: {e}")
            yield

    async def shutdown(self) -> None:
        """Shutdown telemetry."""
        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()

            if self.meter_provider:
                self.meter_provider.shutdown()

            logger.info("Telemetry shutdown completed")

        except Exception as e:
            logger.error(f"Failed to shutdown telemetry: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if telemetry is initialized."""
        return self._initialized
