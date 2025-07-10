# OpenTelemetry Telemetry

MetaMCP integrates comprehensive observability using OpenTelemetry for tracing, metrics, and logging across the entire application.

## Overview

The telemetry system provides:

- **Distributed Tracing**: Track request flows across services
- **Metrics Collection**: Monitor performance and usage patterns
- **Structured Logging**: Consistent log format with correlation IDs
- **Instrumentation**: Automatic instrumentation of FastAPI, HTTPX, and SQLAlchemy

## Configuration

### Environment Variables

```bash
# Enable/disable telemetry
TELEMETRY_ENABLED=true

# OTLP endpoint for distributed tracing and metrics
OTLP_ENDPOINT=http://localhost:4317

# OTLP connection security
OTLP_INSECURE=true

# Prometheus metrics port
PROMETHEUS_METRICS_PORT=9090
```

### Settings

```python
from metamcp.config import get_settings

settings = get_settings()

# Telemetry settings
telemetry_enabled = settings.telemetry_enabled
otlp_endpoint = settings.otlp_endpoint
otlp_insecure = settings.otlp_insecure
prometheus_metrics_port = settings.prometheus_metrics_port
```

## Components

### TelemetryManager

The main telemetry orchestrator that manages:

- OpenTelemetry SDK initialization
- Tracer and Meter providers
- Metric instruments
- Automatic instrumentation

```python
from metamcp.monitoring.telemetry import TelemetryManager

# Initialize telemetry
telemetry_manager = TelemetryManager()
await telemetry_manager.initialize()

# Instrument FastAPI
telemetry_manager.instrument_fastapi(app)

# Record custom metrics
telemetry_manager.record_request(
    method="GET",
    path="/api/tools",
    status_code=200,
    duration=0.123
)
```

### Tracing

Distributed tracing tracks request flows:

```python
from metamcp.monitoring.telemetry import TelemetryManager

telemetry_manager = TelemetryManager()

async with telemetry_manager.trace_operation(
    "tool_execution",
    attributes={"tool_name": "calculator", "user_id": "123"}
) as span:
    # Execute tool
    result = await tool.execute(input_data)
    
    # Add span attributes
    span.set_attribute("result_size", len(result))
```

### Metrics

Built-in metrics include:

#### Request Metrics
- `metamcp_requests_total`: Total request count
- `metamcp_request_duration_seconds`: Request duration histogram

#### Tool Execution Metrics
- `metamcp_tool_executions_total`: Tool execution count
- `metamcp_tool_execution_duration_seconds`: Tool execution duration

#### Vector Search Metrics
- `metamcp_vector_searches_total`: Vector search count
- `metamcp_vector_search_duration_seconds`: Vector search duration

### Custom Metrics

Record custom metrics:

```python
# Record tool execution
telemetry_manager.record_tool_execution(
    tool_name="calculator",
    success=True,
    duration=0.5
)

# Record vector search
telemetry_manager.record_vector_search(
    query_length=50,
    result_count=10,
    duration=0.1
)
```

## Instrumentation

### Automatic Instrumentation

The system automatically instruments:

- **FastAPI**: Request/response tracing and metrics
- **HTTPX**: HTTP client calls
- **SQLAlchemy**: Database operations

### Manual Instrumentation

Add custom instrumentation:

```python
from opentelemetry import trace

tracer = trace.get_tracer("metamcp")

def custom_function():
    with tracer.start_as_current_span("custom_operation") as span:
        span.set_attribute("custom.attribute", "value")
        # Your code here
```

## Observability Backends

### Prometheus

Metrics are exposed on `/metrics` endpoint:

```bash
# Scrape metrics
curl http://localhost:9090/metrics
```

### Jaeger (Tracing)

Configure Jaeger for distributed tracing:

```yaml
# docker-compose.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
```

### Grafana (Visualization)

Create dashboards for:

- Request rates and latencies
- Tool execution metrics
- Vector search performance
- Error rates and distributions

## Monitoring Dashboards

### Key Metrics to Monitor

1. **Request Performance**
   - Request rate (RPS)
   - Response time percentiles
   - Error rate

2. **Tool Execution**
   - Tool execution rate
   - Execution duration
   - Success/failure rates

3. **Vector Search**
   - Search query rate
   - Search duration
   - Result count distribution

4. **System Health**
   - Memory usage
   - CPU utilization
   - Database connections

### Alerting

Set up alerts for:

- High error rates (>5%)
- Slow response times (>2s)
- Tool execution failures
- Vector search timeouts

## Development

### Local Development

For local development, telemetry can be disabled:

```bash
TELEMETRY_ENABLED=false
```

### Testing

Mock telemetry for testing:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_telemetry():
    telemetry = Mock()
    telemetry.record_request = Mock()
    telemetry.record_tool_execution = Mock()
    return telemetry
```

## Troubleshooting

### Common Issues

1. **OTLP Connection Failed**
   - Check OTLP endpoint configuration
   - Verify network connectivity
   - Check TLS settings

2. **High Memory Usage**
   - Reduce batch size for span processors
   - Configure sampling
   - Monitor span buffer size

3. **Missing Traces**
   - Verify instrumentation is enabled
   - Check sampling configuration
   - Ensure proper span propagation

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
```

## Best Practices

1. **Span Naming**: Use descriptive span names
2. **Attributes**: Add relevant context as attributes
3. **Sampling**: Configure appropriate sampling rates
4. **Error Handling**: Always handle telemetry errors gracefully
5. **Performance**: Minimize telemetry overhead in hot paths

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from metamcp.monitoring.telemetry import TelemetryManager

app = FastAPI()
telemetry_manager = TelemetryManager()

# Instrument FastAPI
telemetry_manager.instrument_fastapi(app)
```

### Custom Middleware

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, telemetry_manager):
        super().__init__(app)
        self.telemetry_manager = telemetry_manager
    
    async def dispatch(self, request: Request, call_next):
        # Custom telemetry logic
        return await call_next(request)
```

This comprehensive telemetry system provides full observability into MetaMCP's operations, enabling effective monitoring, debugging, and performance optimization. 