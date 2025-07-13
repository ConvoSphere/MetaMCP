# Test Structure for MetaMCP

This directory contains all automated tests for the MetaMCP project. Tests are organized by type to ensure maintainability and clarity.

## Directory Structure

### Main Test Categories
- `unit/`         – Unit tests for individual functions, classes, and modules (no external dependencies)
- `integration/`  – Integration tests for component interactions or external systems (e.g., API, DB)
- `regression/`   – Regression tests to secure bug fixes and recurring error cases
- `blackbox/`     – Blackbox and end-to-end tests (e.g., REST/MCP API, container tests)

### Unit Test Subcategories
- `unit/security/`    – Authentication, authorization, and security tests
- `unit/performance/` – Performance, benchmarking, and scalability tests
- `unit/telemetry/`   – Monitoring, metrics, and telemetry tests
- `unit/health/`      – Health check and monitoring tests
- `unit/services/`    – Service layer tests (auth, tools, search)
- `unit/utils/`       – Utility function tests (cache, circuit breaker, logging)

### Blackbox Test Subcategories
- `blackbox/rest_api/`     – REST API endpoint tests
- `blackbox/mcp_api/`      – MCP protocol tests
- `blackbox/integration/`  – End-to-end workflow tests
- `blackbox/performance/`  – Load and stress tests

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/unit

# Security tests only
pytest tests/unit/security

# Performance tests only
pytest tests/unit/performance

# Telemetry tests only
pytest tests/unit/telemetry

# Integration tests only
pytest tests/integration

# Regression tests only
pytest tests/regression

# Blackbox tests only
pytest tests/blackbox
```

### Test with Coverage
```bash
pytest --cov=metamcp tests/
```

### Test with Verbose Output
```bash
pytest -v tests/
```

## Test Organization

### Security Tests (`tests/unit/security/`)
- Authentication mechanisms (JWT, password hashing)
- Authorization and access control
- Input validation and sanitization
- Cryptographic functions
- Security headers and CORS
- Rate limiting
- Audit logging
- Configuration security

### Performance Tests (`tests/unit/performance/`)
- Telemetry performance overhead
- Tool registry performance
- Vector search performance
- LLM service performance
- Memory usage tests
- Concurrency and load testing
- Scalability tests
- Benchmark tests

### Telemetry Tests (`tests/unit/telemetry/`)
- Telemetry manager initialization
- Request and metric recording
- Operation tracing
- FastAPI instrumentation
- Error handling
- Integration with server components

## Notes
- Common fixtures and helper functions can be placed in respective `conftest.py` files
- Test migration to the new structure is done step by step
- Each test category has its own `__init__.py` file for proper module organization 