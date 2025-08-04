"""
Test Data Factory for MetaMCP

This module provides factories for generating various types of test data including:
- User data
- Tool data
- Search queries
- Authentication tokens
- Performance test data
- Security test data
"""

import random
import time
import uuid
from datetime import datetime, timedelta

import faker


class TestDataFactory:
    """Factory for creating test data."""

    def __init__(self):
        self.fake = faker.Faker()
        self.fake.seed_instance(42)  # For reproducible results

    def create_user_data(self, username: str | None = None, **kwargs) -> dict:
        """Create user test data."""
        if username is None:
            username = f"testuser_{int(time.time())}_{random.randint(1000, 9999)}"

        base_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": "TestPassword123!",
            "full_name": self.fake.name(),
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        base_data.update(kwargs)
        return base_data

    def create_admin_user_data(self, username: str | None = None, **kwargs) -> dict:
        """Create admin user test data."""
        user_data = self.create_user_data(username, **kwargs)
        user_data.update(
            {"is_admin": True, "permissions": ["admin", "read", "write", "delete"]}
        )
        return user_data

    def create_tool_data(self, name: str | None = None, **kwargs) -> dict:
        """Create tool test data."""
        if name is None:
            name = f"testtool_{int(time.time())}_{random.randint(1000, 9999)}"

        base_data = {
            "name": name,
            "description": self.fake.text(max_nb_chars=200),
            "version": "1.0.0",
            "author": self.fake.name(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input parameter"}
                },
                "required": ["input"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "Output result"}
                },
            },
            "endpoints": [
                {
                    "url": f"http://localhost:8001/{name.lower().replace(' ', '-')}",
                    "method": "POST",
                    "timeout": 30,
                }
            ],
            "tags": ["test", "automated"],
            "category": "utility",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        base_data.update(kwargs)
        return base_data

    def create_calculator_tool_data(self, **kwargs) -> dict:
        """Create calculator tool test data."""
        tool_data = self.create_tool_data("Calculator", **kwargs)
        tool_data.update(
            {
                "description": "A simple calculator tool for mathematical operations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "Mathematical operation",
                        },
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["operation", "a", "b"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "number",
                            "description": "Calculation result",
                        },
                        "operation": {
                            "type": "string",
                            "description": "Performed operation",
                        },
                    },
                },
                "tags": ["math", "calculator", "utility"],
                "category": "mathematics",
            }
        )
        return tool_data

    def create_search_tool_data(self, **kwargs) -> dict:
        """Create search tool test data."""
        tool_data = self.create_tool_data("Search Tool", **kwargs)
        tool_data.update(
            {
                "description": "A tool for searching through data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results"},
                        "filters": {"type": "object", "description": "Search filters"},
                    },
                    "required": ["query"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "results": {"type": "array", "description": "Search results"},
                        "total": {
                            "type": "integer",
                            "description": "Total results count",
                        },
                    },
                },
                "tags": ["search", "data", "utility"],
                "category": "data",
            }
        )
        return tool_data

    def create_search_query(self, query: str | None = None, **kwargs) -> dict:
        """Create search query test data."""
        if query is None:
            query = self.fake.word()

        base_data = {
            "query": query,
            "filters": {},
            "limit": 10,
            "offset": 0,
            "sort_by": "relevance",
            "sort_order": "desc",
        }

        base_data.update(kwargs)
        return base_data

    def create_authentication_data(self, username: str | None = None, **kwargs) -> dict:
        """Create authentication test data."""
        if username is None:
            username = f"authuser_{int(time.time())}"

        base_data = {
            "username": username,
            "password": "AuthPassword123!",
            "grant_type": "password",
        }

        base_data.update(kwargs)
        return base_data

    def create_token_data(self, username: str, **kwargs) -> dict:
        """Create token test data."""
        base_data = {
            "sub": username,
            "permissions": ["read", "write"],
            "exp": datetime.now() + timedelta(hours=1),
            "iat": datetime.now(),
            "jti": str(uuid.uuid4()),
        }

        base_data.update(kwargs)
        return base_data

    def create_performance_test_data(self, size: int = 100) -> list[dict]:
        """Create performance test data."""
        data = []
        for i in range(size):
            data.append(
                {
                    "id": i,
                    "name": f"perf_item_{i}",
                    "value": random.random() * 1000,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "category": random.choice(["A", "B", "C"]),
                        "priority": random.randint(1, 5),
                        "tags": [self.fake.word() for _ in range(random.randint(1, 3))],
                    },
                }
            )
        return data

    # Test data for security testing
    SECURITY_TEST_DATA = {
        "sql_injection_attempts": [
            "'; DROP TABLE users; --",
            "'; DELETE FROM users; --",
            "'; UPDATE users SET role='admin'; --",
            "'; INSERT INTO users VALUES ('attacker', 'password'); --",
            "'; ALTER TABLE users ADD COLUMN hacked BOOLEAN; --",
        ],
        "xss_attempts": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
        ],
        "path_traversal_attempts": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ],
        "command_injection_attempts": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(whoami)",
        ],
        "no_sql_injection_attempts": [
            '{"$where": "1==1"}',
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$regex": ".*"}',
            '{"$exists": true}',
        ],
    }

    def create_load_test_data(self, num_users: int = 10, num_tools: int = 50) -> dict:
        """Create load test data."""
        users = []
        tools = []

        for i in range(num_users):
            users.append(self.create_user_data(f"loaduser_{i}"))

        for i in range(num_tools):
            tools.append(self.create_tool_data(f"loadtool_{i}"))

        return {
            "users": users,
            "tools": tools,
            "search_queries": [self.create_search_query() for _ in range(20)],
            "auth_requests": [
                self.create_authentication_data(f"loaduser_{i}")
                for i in range(num_users)
            ],
        }

    def create_stress_test_data(self, size: int = 1000) -> dict:
        """Create stress test data."""
        return {
            "large_dataset": [self.create_tool_data() for _ in range(size)],
            "concurrent_users": [self.create_user_data() for _ in range(100)],
            "rapid_requests": [self.create_search_query() for _ in range(500)],
        }

    def create_benchmark_data(self) -> dict:
        """Create benchmark test data."""
        return {
            "small_dataset": [self.create_tool_data() for _ in range(10)],
            "medium_dataset": [self.create_tool_data() for _ in range(100)],
            "large_dataset": [self.create_tool_data() for _ in range(1000)],
            "search_queries": [
                self.create_search_query("calculator"),
                self.create_search_query("search"),
                self.create_search_query("utility"),
                self.create_search_query("math"),
                self.create_search_query("data"),
            ],
        }

    def create_integration_test_data(self) -> dict:
        """Create integration test data."""
        return {
            "users": [
                self.create_user_data("integration_user_1"),
                self.create_admin_user_data("integration_admin"),
                self.create_user_data("integration_user_2", is_active=False),
            ],
            "tools": [
                self.create_calculator_tool_data(),
                self.create_search_tool_data(),
                self.create_tool_data("Integration Test Tool"),
            ],
            "workflows": [
                {
                    "name": "User Registration and Tool Creation",
                    "steps": [
                        "create_user",
                        "authenticate_user",
                        "create_tool",
                        "search_tools",
                        "execute_tool",
                    ],
                },
                {
                    "name": "Admin Operations",
                    "steps": [
                        "admin_login",
                        "list_all_users",
                        "list_all_tools",
                        "system_statistics",
                    ],
                },
            ],
        }

    def create_error_test_data(self) -> dict:
        """Create error test data."""
        return {
            "invalid_users": [
                {
                    "username": "",
                    "email": "test@example.com",
                    "password": "TestPass123!",
                },
                {
                    "username": "test",
                    "email": "invalid-email",
                    "password": "TestPass123!",
                },
                {"username": "test", "email": "test@example.com", "password": "weak"},
                {
                    "username": "a" * 1000,
                    "email": "test@example.com",
                    "password": "TestPass123!",
                },
            ],
            "invalid_tools": [
                {"name": "", "description": "Test tool"},
                {"name": "test", "description": "Test tool", "input_schema": "invalid"},
                {"name": "test", "description": "Test tool", "endpoints": []},
            ],
            "invalid_queries": [
                {"query": "", "limit": 10},
                {"query": "test", "limit": -1},
                {"query": "test", "offset": -10},
            ],
        }

    def create_mock_response_data(self, status_code: int = 200, **kwargs) -> dict:
        """Create mock response data."""
        base_data = {
            "status_code": status_code,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": str(uuid.uuid4()),
            },
            "data": {
                "status": "success" if status_code < 400 else "error",
                "message": (
                    "Operation completed successfully"
                    if status_code < 400
                    else "Operation failed"
                ),
                "timestamp": datetime.now().isoformat(),
            },
        }

        base_data.update(kwargs)
        return base_data

    def create_mock_request_data(self, method: str = "GET", **kwargs) -> dict:
        """Create mock request data."""
        base_data = {
            "method": method,
            "url": "http://localhost:8000/api/v1/test",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token",
                "User-Agent": "TestClient/1.0",
            },
            "params": {},
            "data": {},
        }

        base_data.update(kwargs)
        return base_data

    def create_test_configuration(self) -> dict:
        """Create test configuration data."""
        return {
            "database": {
                "url": "sqlite:///./test.db",
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10,
            },
            "cache": {
                "enabled": True,
                "backend": "memory",
                "ttl": 300,
                "max_size": 1000,
            },
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100,
                "burst_size": 10,
            },
            "security": {
                "secret_key": "test-secret-key-for-testing-only",
                "algorithm": "HS256",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_days": 7,
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "test.log",
            },
        }

    def create_test_metrics(self) -> dict:
        """Create test metrics data."""
        return {
            "response_times": [random.uniform(0.1, 2.0) for _ in range(100)],
            "memory_usage": [random.uniform(50, 500) for _ in range(100)],
            "cpu_usage": [random.uniform(10, 90) for _ in range(100)],
            "error_counts": random.randint(0, 10),
            "success_counts": random.randint(90, 100),
            "throughput": random.uniform(100, 1000),
        }

    def create_test_environment(self) -> dict:
        """Create test environment data."""
        return {
            "python_version": "3.11.0",
            "platform": "linux",
            "dependencies": {
                "fastapi": "0.104.0",
                "pydantic": "2.4.0",
                "sqlalchemy": "2.0.0",
                "pytest": "7.4.0",
            },
            "environment_variables": {
                "META_MCP_TESTING": "true",
                "META_MCP_LOG_LEVEL": "DEBUG",
                "META_MCP_DATABASE_URL": "sqlite:///./test.db",
            },
        }


# Convenience functions for common test data creation
def create_user_data(**kwargs) -> dict:
    """Create user test data."""
    factory = TestDataFactory()
    return factory.create_user_data(**kwargs)


def create_tool_data(**kwargs) -> dict:
    """Create tool test data."""
    factory = TestDataFactory()
    return factory.create_tool_data(**kwargs)


def create_search_query(**kwargs) -> dict:
    """Create search query test data."""
    factory = TestDataFactory()
    return factory.create_search_query(**kwargs)


def create_authentication_data(**kwargs) -> dict:
    """Create authentication test data."""
    factory = TestDataFactory()
    return factory.create_authentication_data(**kwargs)


def create_security_test_data() -> dict:
    """Create security test data."""
    factory = TestDataFactory()
    return factory.create_security_test_data()


def create_load_test_data(**kwargs) -> dict:
    """Create load test data."""
    factory = TestDataFactory()
    return factory.create_load_test_data(**kwargs)


def create_integration_test_data() -> dict:
    """Create integration test data."""
    factory = TestDataFactory()
    return factory.create_integration_test_data()
