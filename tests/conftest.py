"""
Comprehensive test configuration and fixtures for MetaMCP.

This module provides shared fixtures, test utilities, and configuration
for all test suites including unit, integration, and blackbox tests.
"""

import asyncio
import os
import sys
import tempfile
import time
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
from metamcp.config import Settings
from metamcp.main import create_app
from metamcp.services.auth_service import AuthService
from metamcp.services.search_service import SearchService
from metamcp.services.tool_service import ToolService
from metamcp.utils.cache import Cache
from metamcp.utils.circuit_breaker import CircuitBreaker
from metamcp.utils.rate_limiter import RateLimiter

sys.path.insert(0, str(project_root))


# Test Configuration
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test settings with overrides."""
    return Settings(
        # Database
        database_url="sqlite:///./test.db",
        # Vector Database
        vector_database_url="http://localhost:8080",
        # Security
        secret_key="test-secret-key-for-testing-only",
        algorithm="HS256",
        access_token_expire_minutes=30,
        # Logging
        log_level="DEBUG",
        # Testing
        testing=True,
        # Rate Limiting
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=100,
        # Cache
        cache_enabled=True,
        cache_ttl_seconds=300,
        # Circuit Breaker
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=5,
        circuit_breaker_recovery_timeout=60,
        # Admin UI
        admin_ui_enabled=True,
        admin_ui_port=8081,
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    """Create a test FastAPI application."""
    return create_app(settings=test_settings)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Database Fixtures
@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///./test.db", echo=False)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


# Service Fixtures
@pytest.fixture
async def auth_service(test_settings: Settings) -> AuthService:
    """Create AuthService instance for testing."""
    return AuthService(settings=test_settings)


@pytest.fixture
async def tool_service(test_settings: Settings) -> ToolService:
    """Create ToolService instance for testing."""
    return ToolService(settings=test_settings)


@pytest.fixture
async def search_service(test_settings: Settings) -> SearchService:
    """Create SearchService instance for testing."""
    return SearchService(settings=test_settings)


# Utility Fixtures
@pytest.fixture
def cache(test_settings: Settings) -> Cache:
    """Create Cache instance for testing."""
    return Cache(settings=test_settings)


@pytest.fixture
def circuit_breaker(test_settings: Settings) -> CircuitBreaker:
    """Create CircuitBreaker instance for testing."""
    return CircuitBreaker(
        failure_threshold=test_settings.circuit_breaker_failure_threshold,
        recovery_timeout=test_settings.circuit_breaker_recovery_timeout,
    )


@pytest.fixture
def rate_limiter(test_settings: Settings) -> RateLimiter:
    """Create RateLimiter instance for testing."""
    return RateLimiter(settings=test_settings)


# Test Data Fixtures
@pytest.fixture
def sample_user_data() -> dict:
    """Provide sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
def sample_tool_data() -> dict:
    """Provide sample tool data for testing."""
    return {
        "name": "Calculator",
        "description": "A simple calculator tool",
        "version": "1.0.0",
        "author": "Test Author",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                },
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["operation", "a", "b"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "number"},
                "operation": {"type": "string"},
            },
        },
        "endpoints": [
            {"url": "http://localhost:8001/calculate", "method": "POST", "timeout": 30}
        ],
        "tags": ["math", "calculator"],
        "category": "utility",
    }


@pytest.fixture
def sample_search_query() -> dict:
    """Provide sample search query for testing."""
    return {
        "query": "calculator tool",
        "filters": {"category": "utility", "tags": ["math"]},
        "limit": 10,
        "offset": 0,
    }


# Mock Fixtures
@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for testing HTTP requests."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value = AsyncMock()
        yield mock_client.return_value


@pytest.fixture
def mock_vector_client():
    """Create a mock vector client for testing."""
    with patch("metamcp.vector.client.VectorClient") as mock_client:
        mock_client.return_value = AsyncMock()
        yield mock_client.return_value


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    with patch("metamcp.llm.service.LLMService") as mock_service:
        mock_service.return_value = AsyncMock()
        yield mock_service.return_value


@pytest.fixture
def mock_db_manager():
    """
    Provide a fully mocked DatabaseManager for unit tests.
    Nutze diese Fixture, um alle DB-Operationen (acquire, fetch, fetchval, execute) zu mocken.
    Beispiel:
        def test_something(mock_db_manager):
            mock_db_manager.fetch.return_value = [{"id": 1}]
            ...
    """
    mock_manager = AsyncMock()
    mock_manager.acquire.return_value.__aenter__.return_value = mock_manager
    mock_manager.fetch = AsyncMock()
    mock_manager.fetchval = AsyncMock()
    mock_manager.execute = AsyncMock()
    yield mock_manager


# Authentication Fixtures
@pytest.fixture
async def test_user_token(auth_service: AuthService, sample_user_data: dict) -> str:
    """Create a test user and return authentication token."""
    # Create test user
    user = await auth_service.create_user(sample_user_data)

    # Generate token
    token_data = {"sub": user["username"], "permissions": user["permissions"]}
    token = await auth_service.create_access_token(token_data)

    return token


@pytest.fixture
async def admin_token(auth_service: AuthService) -> str:
    """Create admin user and return authentication token."""
    admin_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "is_active": True,
        "is_admin": True,
    }

    # Create admin user
    user = await auth_service.create_user(admin_data)

    # Generate token
    token_data = {"sub": user["username"], "permissions": user["permissions"]}
    token = await auth_service.create_access_token(token_data)

    return token


# Tool Fixtures
@pytest.fixture
async def registered_tool(tool_service: ToolService, sample_tool_data: dict) -> str:
    """Register a test tool and return its ID."""
    tool_id = await tool_service.register_tool(sample_tool_data, "testuser")
    return tool_id


# Performance Test Fixtures
@pytest.fixture
def performance_metrics():
    """Provide performance metrics tracking."""
    return {
        "response_times": [],
        "memory_usage": [],
        "cpu_usage": [],
        "error_counts": 0,
        "success_counts": 0,
    }


@pytest.fixture
def load_test_config():
    """Provide load test configuration."""
    return {
        "concurrent_users": 10,
        "requests_per_user": 100,
        "ramp_up_time": 30,
        "test_duration": 300,
        "target_rps": 50,
    }


# Security Test Fixtures
@pytest.fixture
def security_test_data():
    """Provide security test data."""
    return {
        "sql_injection_payloads": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ],
        "path_traversal_payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
        ],
        "invalid_tokens": [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "",
            None,
        ],
    }


# Integration Test Fixtures
@pytest.fixture
async def test_environment():
    """Set up test environment with all services."""
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment variables
        os.environ["META_MCP_TESTING"] = "true"
        os.environ["META_MCP_DATABASE_URL"] = f"sqlite:///{temp_dir}/test.db"
        os.environ["META_MCP_LOG_LEVEL"] = "DEBUG"

        yield {
            "temp_dir": temp_dir,
            "database_url": f"sqlite:///{temp_dir}/test.db",
        }


# Test Utilities
class TestUtils:
    """Utility class for common test operations."""

    @staticmethod
    def assert_success_response(response, expected_status: int = 200):
        """Assert successful HTTP response and return JSON data."""
        assert response.status_code == expected_status
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        return data.get("data", data)

    @staticmethod
    def assert_error_response(
        response, expected_status: int, expected_error: str | None = None
    ):
        """Assert error HTTP response and return error data."""
        assert response.status_code == expected_status
        data = response.json()
        assert "status" in data
        assert data["status"] == "error"
        if expected_error:
            assert "error" in data
            assert expected_error in data["error"]
        return data

    @staticmethod
    def create_test_file(content: str, extension: str = ".txt") -> Path:
        """Create a temporary test file."""
        temp_file = Path(tempfile.mktemp(suffix=extension))
        temp_file.write_text(content)
        return temp_file

    @staticmethod
    def measure_time(func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    @staticmethod
    async def measure_async_time(func, *args, **kwargs):
        """Measure execution time of an async function."""
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time


@pytest.fixture
def test_utils():
    """Provide TestUtils instance."""
    return TestUtils()


# Test Markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmarks")
    config.addinivalue_line("markers", "load: marks tests as load tests")
    config.addinivalue_line("markers", "stress: marks tests as stress tests")


# Test Data Factories
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user_data(username: str = None, **kwargs) -> dict:
        """Create user test data."""
        if username is None:
            username = f"testuser_{int(time.time())}"

        return {
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpassword123",
            "full_name": f"Test User {username}",
            "is_active": True,
            "is_admin": False,
            **kwargs,
        }

    @staticmethod
    def create_tool_data(name: str = None, **kwargs) -> dict:
        """Create tool test data."""
        if name is None:
            name = f"testtool_{int(time.time())}"

        return {
            "name": name,
            "description": f"A test tool called {name}",
            "version": "1.0.0",
            "author": "Test Author",
            "input_schema": {
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
            },
            "output_schema": {
                "type": "object",
                "properties": {"result": {"type": "string"}},
            },
            "endpoints": [
                {"url": "http://localhost:8001/test", "method": "POST", "timeout": 30}
            ],
            "tags": ["test"],
            "category": "utility",
            **kwargs,
        }

    @staticmethod
    def create_search_query(query: str = "test", **kwargs) -> dict:
        """Create search query test data."""
        return {"query": query, "filters": {}, "limit": 10, "offset": 0, **kwargs}


@pytest.fixture
def test_data_factory():
    """Provide TestDataFactory instance."""
    return TestDataFactory()


# Cleanup Fixtures
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup logic here if needed
    pass


# Test Configuration
@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "timeout": 30,
        "retry_attempts": 3,
        "max_concurrent_requests": 10,
        "test_data_size": 100,
        "performance_thresholds": {
            "response_time_ms": 1000,
            "memory_mb": 512,
            "cpu_percent": 80,
        },
    }
