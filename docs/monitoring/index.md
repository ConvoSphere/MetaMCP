# Monitoring & Observability

MetaMCP provides comprehensive monitoring and observability capabilities to ensure reliable operation and performance optimization.

## Overview

The monitoring system includes:

- **OpenTelemetry Integration**: Distributed tracing, metrics, and logging
- **Health Checks**: Component health monitoring
- **Performance Metrics**: Request timing and resource usage
- **Error Tracking**: Exception monitoring and alerting
- **Audit Logging**: Security and compliance logging

## Components

### [Telemetry](./telemetry.md)

OpenTelemetry-based observability with:
- Distributed tracing across services
- Custom metrics for tool execution and vector search
- Automatic instrumentation of FastAPI, HTTPX, and SQLAlchemy
- Integration with Prometheus, Jaeger, and Grafana

### Health Monitoring

Built-in health checks for:
- Database connectivity
- Vector database availability
- LLM service status
- Policy engine health
- Tool registry status

### Metrics Collection

Key metrics include:
- Request rates and latencies
- Tool execution performance
- Vector search statistics
- System resource usage
- Error rates and distributions

### Logging

Structured logging with:
- Correlation IDs for request tracing
- Log levels and formatting
- Audit trail for security events
- Performance logging

## Quick Start

### Enable Monitoring

```bash
# Enable telemetry
export TELEMETRY_ENABLED=true

# Configure OTLP endpoint
export OTLP_ENDPOINT=http://localhost:4317

# Set Prometheus metrics port
export PROMETHEUS_METRICS_PORT=9090
```

### Access Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Health check
curl http://localhost:8000/health

# Application status
curl http://localhost:8000/
```

### View Traces

1. Start Jaeger:
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest
```

2. Access Jaeger UI: http://localhost:16686

## Configuration

### Environment Variables

```bash
# Telemetry
TELEMETRY_ENABLED=true
OTLP_ENDPOINT=http://localhost:4317
OTLP_INSECURE=true
PROMETHEUS_METRICS_PORT=9090

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Health Checks
HEALTH_CHECK_INTERVAL=30
```

### Settings

```python
from metamcp.config import get_settings

settings = get_settings()

# Monitoring settings
telemetry_enabled = settings.telemetry_enabled
otlp_endpoint = settings.otlp_endpoint
prometheus_metrics_port = settings.prometheus_metrics_port
log_level = settings.log_level
```

## Dashboards

### Grafana Dashboards

Recommended dashboards:

1. **Application Overview**
   - Request rates and response times
   - Error rates and status codes
   - Active connections

2. **Tool Performance**
   - Tool execution rates
   - Execution duration percentiles
   - Success/failure rates by tool

3. **Vector Search**
   - Search query rates
   - Search duration
   - Result count distribution

4. **System Health**
   - CPU and memory usage
   - Database connections
   - Disk I/O

### Alerting Rules

Configure alerts for:

```yaml
# High error rate
- alert: HighErrorRate
  expr: rate(metamcp_requests_total{status_code=~"5.."}[5m]) > 0.05

# Slow response times
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, metamcp_request_duration_seconds) > 2

# Tool execution failures
- alert: ToolExecutionFailures
  expr: rate(metamcp_tool_executions_total{success="false"}[5m]) > 0.1
```

## Development

### Local Development

For local development, you can disable telemetry:

```bash
export TELEMETRY_ENABLED=false
```

### Testing

Mock monitoring components for testing:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_telemetry():
    return Mock()

@pytest.fixture
def mock_health_check():
    return Mock()
```

## Troubleshooting

### Common Issues

1. **Missing Metrics**
   - Check if telemetry is enabled
   - Verify Prometheus endpoint is accessible
   - Check for configuration errors

2. **No Traces in Jaeger**
   - Verify OTLP endpoint configuration
   - Check network connectivity
   - Ensure proper instrumentation

3. **High Memory Usage**
   - Reduce telemetry batch sizes
   - Configure sampling
   - Monitor span buffer usage

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("metamcp.monitoring").setLevel(logging.DEBUG)
```

## Best Practices

1. **Performance**: Minimize telemetry overhead in hot paths
2. **Sampling**: Use appropriate sampling rates for high-volume services
3. **Error Handling**: Always handle telemetry errors gracefully
4. **Security**: Sanitize sensitive data in logs and traces
5. **Retention**: Configure appropriate log and trace retention policies

## Integration

### Prometheus

Add to prometheus.yml:

```yaml
scrape_configs:
  - job_name: 'metamcp'
    static_configs:
      - targets: ['localhost:9090']
```

### Grafana

Import dashboards for:
- Application metrics
- Tool performance
- System health
- Error tracking

### AlertManager

Configure alerting for:
- High error rates
- Slow response times
- Service unavailability
- Resource exhaustion

This monitoring system provides comprehensive observability into MetaMCP's operations, enabling effective monitoring, debugging, and performance optimization. 