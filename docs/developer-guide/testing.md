# Testing Guide

## Overview

MetaMCP includes a comprehensive testing strategy covering unit tests, integration tests, and performance tests. The testing framework ensures code quality, reliability, and maintainability.

## Testing Strategy

### Test Pyramid

```
    ┌─────────────┐
    │ Performance │  ← Few, critical path tests
    │   Tests     │
    └─────────────┘
         │
    ┌─────────────┐
    │Integration  │  ← API and service integration
    │   Tests     │
    └─────────────┘
         │
    ┌─────────────┐
    │  Unit Tests │  ← Many, fast, isolated tests
    │             │
    └─────────────┘
```

### Test Categories

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test API endpoints and service interactions
3. **Performance Tests**: Test system performance under load
4. **Security Tests**: Test authentication, authorization, and security features

## Test Structure

### Directory Organization

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_auth.py             # Authentication tests
├── test_tools.py            # Tool management tests
├── test_health.py           # Health monitoring tests
├── test_services.py         # Service layer tests
├── test_utils.py            # Utility component tests
├── test_performance.py      # Performance tests
└── test_security.py         # Security tests
```

### Test File Naming Convention

- `test_*.py`: Test files
- `*_test.py`: Alternative naming (not used in this project)
- `conftest.py`: Pytest configuration and shared fixtures

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=metamcp

# Run specific test file
pytest tests/test_auth.py

# Run specific test function
pytest tests/test_auth.py::TestAuthService::test_authenticate_user_success
```

### Test Environment Setup

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Set test environment variables
export META_MCP_TESTING=true
export META_MCP_DATABASE_URL=sqlite:///test.db

# Run tests in parallel
pytest -n auto
```

### Coverage Reporting

```bash
# Generate coverage report
pytest --cov=metamcp --cov-report=html

# View coverage report
open htmlcov/index.html

# Generate coverage badge
pytest --cov=metamcp --cov-report=term-missing
```

## Unit Tests

### Authentication Tests (`test_auth.py`)

Tests for the authentication system including user login, token management, and permissions.

#### Key Test Cases:

```python
class TestAuthService:
    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication."""
        user = await auth_service.authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
    
    async def test_verify_token_valid(self, auth_service):
        """Test valid token verification."""
        data = {"sub": "test_user"}
        token = await auth_service.create_access_token(data)
        payload = await auth_service.verify_token(token)
        assert payload["sub"] == "test_user"
    
    async def test_check_permission_admin(self, auth_service):
        """Test permission checking for admin user."""
        has_permission = await auth_service.check_permission("admin_user", "tools", "read")
        assert has_permission is True
```

#### Test Coverage:
- User authentication (success/failure)
- Token creation and verification
- Token revocation and blacklisting
- Permission checking
- User management (CRUD operations)
- Login history tracking

### Tool Management Tests (`test_tools.py`)

Tests for tool registration, execution, and management functionality.

#### Key Test Cases:

```python
class TestToolService:
    async def test_register_tool_success(self, tool_service, sample_tool_data):
        """Test successful tool registration."""
        tool_id = await tool_service.register_tool(sample_tool_data, "test_user")
        assert tool_id is not None
        
    async def test_execute_tool_success(self, mock_httpx, tool_service, sample_tool_data):
        """Test successful tool execution."""
        result = await tool_service.execute_tool("test_tool", {"param": "value"}, "test_user")
        assert result["status"] == "success"
        assert "execution_time" in result
```

#### Test Coverage:
- Tool registration and validation
- Tool execution with HTTP calls
- Tool search and discovery
- Tool statistics and metrics
- Error handling and edge cases

### Health Monitoring Tests (`test_health.py`)

Tests for health check endpoints and system monitoring.

#### Key Test Cases:

```python
class TestHealthEndpoints:
    async def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    async def test_detailed_health(self, client):
        """Test detailed health status."""
        response = await client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "uptime" in data
        assert "components" in data
```

#### Test Coverage:
- Basic health check endpoint
- Detailed health status
- Readiness and liveness probes
- Component health monitoring
- Uptime calculation

### Service Layer Tests (`test_services.py`)

Tests for the service layer components including ToolService, AuthService, and SearchService.

#### Key Test Cases:

```python
class TestSearchService:
    async def test_search_tools_semantic(self, search_service):
        """Test semantic search."""
        results = await search_service.search_tools(
            query="database query",
            search_type="semantic"
        )
        assert "search_id" in results
        assert results["search_type"] == "semantic"
    
    def test_calculate_similarity(self, search_service):
        """Test similarity calculation."""
        similarity = search_service._calculate_similarity("query", tool_data)
        assert 0.0 <= similarity <= 1.0
```

#### Test Coverage:
- Service layer business logic
- Search functionality (semantic, keyword, hybrid)
- Service interactions
- Error handling in services
- Service statistics and metrics

### Utility Tests (`test_utils.py`)

Tests for utility components including circuit breaker and caching.

#### Key Test Cases:

```python
class TestCircuitBreaker:
    async def test_circuit_opens_after_threshold(self, circuit_breaker):
        """Test circuit opens after failure threshold."""
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failure_func)
        assert circuit_breaker.state == CircuitState.OPEN
    
    async def test_circuit_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions to half-open after timeout."""
        # Open circuit, then simulate timeout
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED

class TestMemoryCacheBackend:
    async def test_set_and_get(self, cache_backend):
        """Test setting and getting cache entries."""
        await cache_backend.set("key", "value")
        value = await cache_backend.get("key")
        assert value == "value"
    
    async def test_expiration(self, cache_backend):
        """Test cache entry expiration."""
        await cache_backend.set("key", "value", ttl=1)
        await asyncio.sleep(1.1)
        assert await cache_backend.get("key") is None
```

#### Test Coverage:
- Circuit breaker pattern implementation
- Cache backend functionality
- Cache expiration and eviction
- Circuit breaker state transitions
- Cache statistics and monitoring

## Integration Tests

### API Integration Tests

Tests that verify the complete API functionality including authentication, request/response handling, and error scenarios.

#### Test Setup:

```python
@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    async with TestClient(app) as client:
        yield client

@pytest.fixture
async def authenticated_client(client):
    """Create authenticated test client."""
    # Login and get token
    response = await client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.json()["data"]["access_token"]
    
    # Set authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

#### Key Test Cases:

```python
class TestAPIIntegration:
    async def test_tool_lifecycle(self, authenticated_client):
        """Test complete tool lifecycle."""
        # Register tool
        tool_data = {"name": "test_tool", "description": "Test tool"}
        response = await authenticated_client.post("/tools", json=tool_data)
        assert response.status_code == 200
        
        # Get tool
        response = await authenticated_client.get("/tools/test_tool")
        assert response.status_code == 200
        
        # Execute tool
        response = await authenticated_client.post("/tools/test_tool/execute", 
                                                json={"arguments": {}})
        assert response.status_code == 200
        
        # Delete tool
        response = await authenticated_client.delete("/tools/test_tool")
        assert response.status_code == 200
```

### Service Integration Tests

Tests that verify service layer interactions and business logic.

#### Key Test Cases:

```python
class TestServiceIntegration:
    async def test_tool_execution_with_circuit_breaker(self, tool_service, auth_service):
        """Test tool execution with circuit breaker protection."""
        # Register tool
        tool_id = await tool_service.register_tool(tool_data, "user")
        
        # Execute tool (should work)
        result = await tool_service.execute_tool("test_tool", {}, "user")
        assert result["status"] == "success"
        
        # Simulate failures to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await tool_service.execute_tool("test_tool", {"fail": True}, "user")
        
        # Next execution should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await tool_service.execute_tool("test_tool", {}, "user")
```

## Performance Tests

### Load Testing

Tests that verify system performance under various load conditions.

#### Test Setup:

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    async def test_concurrent_tool_execution(self, tool_service):
        """Test concurrent tool execution performance."""
        start_time = time.time()
        
        # Execute 100 concurrent tool calls
        tasks = []
        for i in range(100):
            task = tool_service.execute_tool("test_tool", {"param": i}, "user")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all executions succeeded
        assert all(r["status"] == "success" for r in results)
        
        # Verify performance requirements
        execution_time = end_time - start_time
        assert execution_time < 10.0  # Should complete within 10 seconds
```

### Memory and Resource Tests

Tests that verify memory usage and resource management.

#### Key Test Cases:

```python
class TestResourceManagement:
    def test_cache_memory_usage(self, cache_backend):
        """Test cache memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Add many cache entries
        for i in range(1000):
            cache_backend.set(f"key{i}", "value" * 1000)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 50 * 1024 * 1024  # 50MB limit
```

## Security Tests

### Authentication and Authorization Tests

Tests that verify security features and access controls.

#### Key Test Cases:

```python
class TestSecurity:
    async def test_invalid_token_rejection(self, client):
        """Test that invalid tokens are rejected."""
        client.headers["Authorization"] = "Bearer invalid_token"
        response = await client.get("/tools")
        assert response.status_code == 401
    
    async def test_permission_enforcement(self, client):
        """Test that permissions are properly enforced."""
        # Login as regular user
        response = await client.post("/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        token = response.json()["data"]["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Try to access admin endpoint
        response = await client.post("/admin/users", json={})
        assert response.status_code == 403
    
    async def test_sql_injection_prevention(self, tool_service):
        """Test SQL injection prevention."""
        malicious_input = "'; DROP TABLE users; --"
        
        # This should not cause any database issues
        result = await tool_service.search_tools(malicious_input)
        assert isinstance(result, dict)
```

## Test Fixtures and Utilities

### Common Fixtures (`conftest.py`)

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return {
        "name": "test_tool",
        "description": "Test tool for testing",
        "endpoint": "http://localhost:8001",
        "category": "test",
        "capabilities": ["read", "write"],
        "security_level": 2,
        "schema": {"input": {}, "output": {}},
        "metadata": {"version": "1.0.0"},
        "version": "1.0.0",
        "author": "test_author",
        "tags": ["test", "api"]
    }

@pytest.fixture
def mock_httpx():
    """Mock httpx for HTTP calls."""
    with patch('metamcp.services.tool_service.httpx') as mock:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.text = '{"result": "success"}'
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock.AsyncClient.return_value.__aenter__.return_value = mock_client
        
        yield mock

@pytest.fixture
def circuit_breaker():
    """Create circuit breaker for testing."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=10.0,
        monitor_interval=5.0
    )
    return CircuitBreaker("test_circuit", config)
```

### Test Utilities

```python
def create_test_user(username="test_user", roles=["user"]):
    """Create test user data."""
    return {
        "username": username,
        "password": "test123",
        "roles": roles,
        "permissions": {
            "tools": ["read", "execute"],
            "admin": []
        }
    }

def assert_error_response(response, error_code, status_code=400):
    """Assert error response format."""
    assert response.status_code == status_code
    data = response.json()
    assert data["error"] == error_code
    assert "message" in data
    assert "timestamp" in data

def assert_success_response(response, status_code=200):
    """Assert success response format."""
    assert response.status_code == status_code
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "timestamp" in data
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=metamcp --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

### Test Organization

1. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
2. **Descriptive Names**: Use descriptive test and function names
3. **Single Responsibility**: Each test should verify one specific behavior
4. **Isolation**: Tests should be independent and not affect each other

### Test Data Management

1. **Fixtures**: Use pytest fixtures for reusable test data
2. **Factories**: Create factory functions for complex test objects
3. **Cleanup**: Ensure proper cleanup after tests
4. **Randomization**: Use random data when appropriate to catch edge cases

### Mocking and Stubbing

1. **External Dependencies**: Mock external services and databases
2. **Time-dependent Code**: Mock time functions for consistent tests
3. **Network Calls**: Mock HTTP requests and responses
4. **File System**: Mock file operations when needed

### Performance Testing

1. **Baseline Measurements**: Establish performance baselines
2. **Load Testing**: Test under realistic load conditions
3. **Resource Monitoring**: Monitor memory, CPU, and I/O usage
4. **Regression Detection**: Detect performance regressions early

## Conclusion

The comprehensive testing strategy ensures MetaMCP's reliability, maintainability, and performance. The combination of unit tests, integration tests, and performance tests provides confidence in the system's behavior across different scenarios and load conditions.

Regular test execution, coverage monitoring, and continuous integration ensure that code quality is maintained throughout the development process. 