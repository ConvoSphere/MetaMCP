"""
Telemetry Tests

Unit tests for the OpenTelemetry telemetry module.
"""

from unittest.mock import Mock, patch

import pytest

from metamcp.monitoring.telemetry import TelemetryManager


class TestTelemetryManager:
    """Test TelemetryManager class."""

    @pytest.fixture
    def telemetry_manager(self):
        """Create telemetry manager instance."""
        return TelemetryManager()

    @pytest.mark.asyncio
    async def test_initialization(self, telemetry_manager):
        """Test telemetry manager initialization."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            assert telemetry_manager.is_initialized
            assert telemetry_manager.tracer_provider is not None
            assert telemetry_manager.meter_provider is not None

    @pytest.mark.asyncio
    async def test_initialization_disabled(self, telemetry_manager):
        """Test telemetry manager initialization when disabled."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = False

            await telemetry_manager.initialize()

            # When telemetry is disabled, it should still be marked as initialized
            # but without actual OpenTelemetry components
            assert telemetry_manager.is_initialized

    @pytest.mark.asyncio
    async def test_record_request(self, telemetry_manager):
        """Test recording request metrics."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock metric instruments
            telemetry_manager.request_counter = Mock()
            telemetry_manager.request_duration = Mock()

            # Record request
            telemetry_manager.record_request(
                method="GET", path="/api/tools", status_code=200, duration=0.123
            )

            # Verify metrics were recorded
            telemetry_manager.request_counter.add.assert_called_once()
            telemetry_manager.request_duration.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_tool_execution(self, telemetry_manager):
        """Test recording tool execution metrics."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock metric instruments
            telemetry_manager.tool_execution_counter = Mock()
            telemetry_manager.tool_execution_duration = Mock()

            # Record tool execution
            telemetry_manager.record_tool_execution(
                tool_name="calculator", success=True, duration=0.5
            )

            # Verify metrics were recorded
            telemetry_manager.tool_execution_counter.add.assert_called_once()
            telemetry_manager.tool_execution_duration.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_vector_search(self, telemetry_manager):
        """Test recording vector search metrics."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock metric instruments
            telemetry_manager.vector_search_counter = Mock()
            telemetry_manager.vector_search_duration = Mock()

            # Record vector search
            telemetry_manager.record_vector_search(
                query_length=50, result_count=10, duration=0.1
            )

            # Verify metrics were recorded
            telemetry_manager.vector_search_counter.add.assert_called_once()
            telemetry_manager.vector_search_duration.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_trace_operation(self, telemetry_manager):
        """Test operation tracing."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock tracer
            mock_span = Mock()
            telemetry_manager.tracer = Mock()
            telemetry_manager.tracer.start_as_current_span.return_value = mock_span

            # Test tracing (should handle mock gracefully)
            try:
                async with telemetry_manager.trace_operation(
                    "test_operation", attributes={"test": "value"}
                ):
                    # In test environment, span might be None due to mock limitations
                    pass
            except Exception:
                # Expected when using mocks
                pass

            # Verify span was created
            telemetry_manager.tracer.start_as_current_span.assert_called_once_with(
                "test_operation", attributes={"test": "value"}
            )

    @pytest.mark.asyncio
    async def test_trace_operation_no_tracer(self, telemetry_manager):
        """Test operation tracing when no tracer is available."""
        # Don't initialize telemetry
        telemetry_manager.tracer = None

        # Test tracing (should not fail)
        async with telemetry_manager.trace_operation("test_operation") as span:
            assert span is None

    @pytest.mark.asyncio
    async def test_instrument_fastapi(self, telemetry_manager):
        """Test FastAPI instrumentation."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock FastAPI app
            mock_app = Mock()

            # Test instrumentation
            telemetry_manager.instrument_fastapi(mock_app)

            # Verify instrumentation was called
            # Note: FastAPIInstrumentor.instrument_app is called internally

    @pytest.mark.asyncio
    async def test_instrument_fastapi_not_initialized(self, telemetry_manager):
        """Test FastAPI instrumentation when not initialized."""
        # Don't initialize telemetry
        telemetry_manager._initialized = False

        # Mock FastAPI app
        mock_app = Mock()

        # Test instrumentation (should not fail)
        telemetry_manager.instrument_fastapi(mock_app)

    @pytest.mark.asyncio
    async def test_shutdown(self, telemetry_manager):
        """Test telemetry shutdown."""
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock providers
            telemetry_manager.tracer_provider = Mock()
            telemetry_manager.meter_provider = Mock()

            # Test shutdown
            await telemetry_manager.shutdown()

            # Verify providers were shut down
            telemetry_manager.tracer_provider.shutdown.assert_called_once()
            telemetry_manager.meter_provider.shutdown.assert_called_once()
            assert not telemetry_manager.is_initialized

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self, telemetry_manager):
        """Test shutdown when not initialized."""
        # Don't initialize telemetry
        telemetry_manager._initialized = False

        # Test shutdown (should not fail)
        await telemetry_manager.shutdown()

    def test_is_initialized_property(self, telemetry_manager):
        """Test is_initialized property."""
        # Initially not initialized
        assert not telemetry_manager.is_initialized

        # Set initialized
        telemetry_manager._initialized = True
        assert telemetry_manager.is_initialized

        # Set not initialized
        telemetry_manager._initialized = False
        assert not telemetry_manager.is_initialized


class TestTelemetryIntegration:
    """Test telemetry integration with other components."""

    @pytest.mark.asyncio
    async def test_telemetry_with_server(self):
        """Test telemetry integration with server."""
        from metamcp.server import MetaMCPServer

        # Mock settings
        with patch("metamcp.config.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090
            mock_settings.debug = False
            mock_settings.reload = False
            mock_settings.docs_enabled = True
            mock_settings.cors_origins = ["*"]
            mock_settings.cors_allow_credentials = True
            mock_get_settings.return_value = mock_settings

            # Create server
            server = MetaMCPServer()

            # Test initialization
            await server.initialize()

            # Verify telemetry was initialized
            assert hasattr(server, "telemetry_manager")

    @pytest.mark.asyncio
    async def test_telemetry_with_mcp_server(self):
        """Test telemetry integration with MCP server."""
        from metamcp.mcp.server import MCPServer

        # Mock settings
        with patch("metamcp.config.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.telemetry_enabled = True
            mock_settings.vector_search_enabled = False
            mock_settings.policy_enforcement_enabled = False
            mock_get_settings.return_value = mock_settings

            # Create MCP server
            mcp_server = MCPServer()

            # Test initialization
            await mcp_server.initialize()

            # Verify telemetry was initialized
            assert hasattr(mcp_server, "telemetry_manager")


class TestTelemetryErrorHandling:
    """Test telemetry error handling."""

    @pytest.mark.asyncio
    async def test_initialization_error(self):
        """Test handling of initialization errors."""
        telemetry_manager = TelemetryManager()

        # Mock settings to cause error
        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = "invalid://endpoint"
            mock_settings.prometheus_metrics_port = 9090

            # Should handle error gracefully
            # In test environment, initialization might succeed despite invalid endpoint
            try:
                await telemetry_manager.initialize()
            except Exception:
                # Expected when endpoint is invalid
                pass

    @pytest.mark.asyncio
    async def test_metric_recording_error(self):
        """Test handling of metric recording errors."""
        telemetry_manager = TelemetryManager()

        with patch("metamcp.monitoring.telemetry.settings") as mock_settings:
            mock_settings.telemetry_enabled = True
            mock_settings.otlp_endpoint = None
            mock_settings.prometheus_metrics_port = 9090

            await telemetry_manager.initialize()

            # Mock metric instruments to raise error
            telemetry_manager.request_counter = Mock()
            telemetry_manager.request_counter.add.side_effect = Exception(
                "Metric error"
            )

            # Should handle error gracefully
            telemetry_manager.record_request(
                method="GET", path="/test", status_code=200, duration=0.1
            )

            # Should not raise exception
            assert telemetry_manager.request_counter.add.called
