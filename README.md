# MetaMCP - Model Context Protocol Management Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/metamcp/metamcp/workflows/Tests/badge.svg)](https://github.com/metamcp/metamcp/actions)

MetaMCP is a comprehensive tool management and execution platform that provides a unified interface for discovering, registering, and executing tools across multiple Model Context Protocol (MCP) servers. Built with FastAPI and modern Python practices, it offers enterprise-grade features for tool orchestration, workflow composition, authentication, monitoring, and fault tolerance.

## 🚀 Features

### Core Functionality
- **Tool Management**: Register, discover, and manage tools across multiple MCP servers
- **Workflow Composition**: Create complex workflows with conditional logic, parallel execution, and state management
- **Unified API**: RESTful API for all tool and workflow operations with comprehensive documentation
- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Tool Execution**: Execute tools with HTTP calls, retries, and error handling
- **Search & Discovery**: Semantic, keyword, and hybrid search for tools

### Advanced Features
- **Workflow Orchestration**: Complete workflow engine with dependency resolution and parallel execution
- **Circuit Breaker Pattern**: Automatic fault tolerance and recovery mechanisms
- **Caching System**: Multi-backend caching (Memory, Redis) with TTL and eviction policies
- **Health Monitoring**: Comprehensive health checks with uptime tracking and component monitoring
- **Service Layer Architecture**: Clean separation of concerns with dedicated service classes
- **Comprehensive Testing**: Organized test suite with unit, integration, performance, and security tests

### Enterprise Features
- **Security**: Input validation, SQL injection prevention, XSS protection
- **Monitoring**: Prometheus metrics, Grafana dashboards, distributed tracing with OpenTelemetry
- **Scalability**: Docker containerization, Kubernetes deployment support
- **Documentation**: Comprehensive API documentation and developer guides
- **FastMCP 2.0 Integration**: Full compatibility with latest MCP protocol standards

## 📋 Requirements

- Python 3.9+
- FastAPI 0.100+
- FastMCP 2.0+
- Redis (optional, for distributed caching)
- PostgreSQL (optional, for persistent storage)
- OpenTelemetry (for distributed tracing)

## 🛠️ Installation

### Quick Start with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/metamcp/metamcp.git
cd metamcp

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Set environment variables
export META_MCP_SECRET_KEY="your-secret-key-here"
export META_MCP_HOST="0.0.0.0"
export META_MCP_PORT="8000"

# Run the application
python -m metamcp.main
```

### Traditional Installation

```bash
# Clone the repository
git clone https://github.com/metamcp/metamcp.git
cd metamcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export META_MCP_SECRET_KEY="your-secret-key-here"
export META_MCP_HOST="0.0.0.0"
export META_MCP_PORT="8000"

# Run the application
python -m metamcp.main
```

### Docker Installation

```bash
# Build and run with Docker
docker build -t metamcp .
docker run -p 8000:8000 -e META_MCP_SECRET_KEY="your-secret-key" metamcp

# Or use Docker Compose
docker-compose up -d
```

### Development Setup

```bash
# Install development dependencies
uv pip install -r requirements-dev.txt

# Run linting and code quality checks
flake8 metamcp/
ruff check metamcp/
bandit -r metamcp/

# Run tests with organized structure
pytest tests/unit/                    # Unit tests only
pytest tests/unit/security/           # Security tests only
pytest tests/unit/performance/        # Performance tests only
pytest tests/unit/telemetry/          # Telemetry tests only
pytest tests/integration/             # Integration tests only
pytest tests/blackbox/                # Blackbox tests only

# Run all tests
pytest

# Run with hot reload
uvicorn metamcp.main:app --reload --host 0.0.0.0 --port 8000
```

## 🏗️ Architecture

MetaMCP follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Admin UI      │    │   API Gateway   │
│   (CLI, Web)    │    │   (Streamlit)   │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                └───────────────────────┘
                                           │
                    ┌─────────────────────────────────────────────┐
                    │              MetaMCP Core                   │
                    │  ┌─────────────┐  ┌─────────────┐         │
                    │  │   Services  │  │   Utils     │         │
                    │  │   Layer     │  │   Layer     │         │
                    │  └─────────────┘  └─────────────┘         │
                    │  ┌─────────────┐  ┌─────────────┐         │
                    │  │ Composition │  │   Proxy     │         │
                    │  │   Engine    │  │ Management  │         │
                    │  └─────────────┘  └─────────────┘         │
                    └─────────────────────────────────────────────┘
                                           │
                    ┌─────────────────────────────────────────────┐
                    │              Data Layer                    │
                    │  ┌─────────────┐  ┌─────────────┐         │
                    │  │   Cache     │  │   Storage   │         │
                    │  │  (Redis)    │  │  (Memory)   │         │
                    │  └─────────────┘  └─────────────┘         │
                    └─────────────────────────────────────────────┘
                                           │
                    ┌─────────────────────────────────────────────┐
                    │              MCP Servers                   │
                    │  ┌─────────────┐  ┌─────────────┐         │
                    │  │  Database   │  │    API      │         │
                    │  │   Tools     │  │   Tools     │         │
                    │  └─────────────┘  └─────────────┘         │
                    └─────────────────────────────────────────────┘
```

### Core Components

- **API Layer** (`metamcp/api/`): RESTful endpoints for all operations
- **Service Layer** (`metamcp/services/`): Business logic and service classes
- **Composition Engine** (`metamcp/composition/`): Workflow orchestration and execution
- **Proxy Management** (`metamcp/proxy/`): External MCP server management
- **Utility Layer** (`metamcp/utils/`): Reusable components (circuit breaker, caching)
- **MCP Integration** (`metamcp/mcp/`): Model Context Protocol communication
- **Monitoring** (`metamcp/monitoring/`): Health checks and metrics collection
- **Security** (`metamcp/security/`): Authentication and authorization

## 🧪 Testing

MetaMCP includes a comprehensive, well-organized test suite:

### Test Structure
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── security/           # Authentication, authorization, security tests
│   ├── performance/        # Performance, benchmarking, scalability tests
│   ├── telemetry/          # Monitoring, metrics, telemetry tests
│   ├── health/             # Health check tests
│   ├── services/           # Service layer tests
│   └── utils/              # Utility function tests
├── integration/            # Integration tests for component interactions
├── regression/             # Regression tests for bug fixes
└── blackbox/              # End-to-end and container tests
    ├── rest_api/           # REST API endpoint tests
    ├── mcp_api/            # MCP protocol tests
    ├── integration/        # End-to-end workflow tests
    └── performance/        # Load and stress tests
```

### Running Tests
```bash
# All tests
pytest

# Specific test categories
pytest tests/unit/security/           # Security tests
pytest tests/unit/performance/        # Performance tests
pytest tests/unit/telemetry/          # Telemetry tests
pytest tests/integration/             # Integration tests
pytest tests/blackbox/                # Blackbox tests

# With coverage
pytest --cov=metamcp tests/

# With verbose output
pytest -v tests/
```

### Test Coverage
- **192+ passing tests** with comprehensive coverage
- **Security tests**: Authentication, authorization, input validation
- **Performance tests**: Benchmarks, scaling, concurrency
- **Telemetry tests**: Monitoring, metrics, distributed tracing
- **Integration tests**: Component interactions and workflows
- **Blackbox tests**: End-to-end API and container testing

## 📚 API Documentation

### Authentication

All API endpoints require JWT authentication:

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token
curl -X GET "http://localhost:8000/api/v1/tools" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Tool Management

```python
# Register a tool
tool_data = {
    "name": "database_query",
    "description": "Execute SQL queries on database",
    "endpoint": "http://localhost:8001",
    "category": "database",
    "capabilities": ["read", "write"],
    "security_level": 2,
    "schema": {"input": {}, "output": {}},
    "metadata": {"version": "1.0.0"},
    "version": "1.0.0",
    "author": "MetaMCP Team",
    "tags": ["database", "sql"]
}

response = requests.post(
    "http://localhost:8000/api/v1/tools",
    json=tool_data,
    headers={"Authorization": f"Bearer {token}"}
)

# Execute a tool
execution_data = {
    "arguments": {
        "query": "SELECT * FROM users LIMIT 10",
        "database": "test_db"
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/tools/database_query/execute",
    json=execution_data,
    headers={"Authorization": f"Bearer {token}"}
)
```

### Workflow Composition

```python
# Register a workflow
workflow_definition = {
    "id": "data-processing-workflow",
    "name": "Data Processing Workflow",
    "description": "Process data through multiple tools",
    "version": "1.0.0",
    "steps": [
        {
            "id": "fetch_data",
            "name": "Fetch Data",
            "step_type": "tool_call",
            "config": {
                "tool_name": "database_query",
                "arguments": {
                    "query": "SELECT * FROM data_table",
                    "database": "$database_name"
                }
            }
        },
        {
            "id": "process_data",
            "name": "Process Data",
            "step_type": "tool_call",
            "config": {
                "tool_name": "data_processor",
                "arguments": {
                    "data": "$fetch_data.result",
                    "operation": "transform"
                }
            },
            "dependencies": ["fetch_data"]
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/workflows",
    json=workflow_definition,
    headers={"Authorization": f"Bearer {token}"}
)
```

## 📊 Monitoring

### Health Checks

- **Basic Health**: `GET /api/v1/health`
- **Detailed Health**: `GET /api/v1/health/detailed`
- **Readiness Probe**: `GET /api/v1/health/ready`
- **Liveness Probe**: `GET /api/v1/health/live`

### Metrics

MetaMCP exposes Prometheus metrics for monitoring:

- Request counts and durations
- Tool execution statistics
- Workflow execution metrics
- Circuit breaker states
- Cache hit rates
- Authentication metrics
- OpenTelemetry distributed tracing

### Logging

Structured logging with configurable levels:

```python
import logging
from metamcp.utils.logging import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application started", extra={"component": "main"})
```

## 🔒 Security

### Authentication

- JWT-based authentication with configurable expiration
- Token refresh mechanism
- Token blacklisting for logout
- Password hashing with bcrypt

### Authorization

- Role-based access control (RBAC)
- Permission-based authorization
- Resource-level permissions
- Admin vs. user role separation

### Security Features

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting (planned)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/contributing.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/metamcp.git
cd metamcp

# Create feature branch
git checkout -b feature/your-feature

# Install development dependencies
uv pip install -r requirements-dev.txt

# Run tests
pytest

# Make changes and commit
git add .
git commit -m "Add your feature"

# Push and create pull request
git push origin feature/your-feature
```

### Code Quality

- **Type Hints**: All functions include type annotations
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: High test coverage with organized test structure
- **Linting**: Black, flake8, ruff, and mypy for code quality
- **Security**: Bandit for security vulnerability scanning
- **Pre-commit Hooks**: Automated code quality checks

## 📖 Documentation

- [Architecture Guide](docs/developer-guide/architecture.md)
- [API Reference](docs/api/index.md)
- [Workflow Composition Guide](docs/composition-improvements.md)
- [Testing Guide](docs/developer-guide/testing.md)
- [Deployment Guide](docs/deployment/)
- [Developer Guide](docs/developer-guide/)

## 🗺️ Roadmap

### Recent Improvements

- ✅ **Enhanced CI/CD Pipeline**: Comprehensive GitHub Actions with multi-stage testing, security scanning, and automated deployments
- ✅ **Database Connection Pooling**: Production-ready PostgreSQL connection pooling with asyncpg
- ✅ **Workflow Persistence**: Complete database-backed workflow storage and execution history
- ✅ **Improved Health Checks**: Real database, vector DB, and LLM service connectivity verification
- ✅ **Automated Documentation**: API documentation generation from docstrings with GitHub Pages deployment
- ✅ **Dependency Management**: Automated dependency updates with security scanning
- ✅ **Organized Test Structure**: Comprehensive test organization with unit, integration, regression, and black-box categories
- ✅ **Enhanced Test Coverage**: 192+ passing tests with security, performance, and telemetry coverage
- ✅ **Workflow Composition**: Complete workflow orchestration engine with dependency resolution
- ✅ **FastMCP 2.0 Integration**: Full compatibility with latest MCP protocol standards
- ✅ **OpenTelemetry Support**: Distributed tracing and observability features
- ✅ **Code Quality**: Improved linting, security scanning, and error handling
- ✅ **Health Monitoring**: Comprehensive health checks and metrics collection
- ✅ **API Routing**: Fixed routing issues and middleware configuration
- ✅ **Authentication**: Enhanced JWT authentication with proper error handling
- ✅ **Performance Optimization**: Circuit breaker patterns and caching strategies
- ✅ **Security Hardening**: Input validation, SQL injection prevention, and XSS protection

### Planned Features

- [ ] **Rate Limiting**: Per-user and per-endpoint rate limits
- [ ] **API Versioning**: Proper API versioning strategy
- [ ] **Admin UI**: Web-based administration interface
- [ ] **Policy Engine**: OPA-based policy evaluation
- [ ] **Multi-tenancy**: Tenant isolation and management
- [ ] **OAuth2 Integration**: Third-party authentication
- [ ] **Webhook Support**: Event-driven integrations
- [ ] **GraphQL API**: Alternative to REST API
- [ ] **Plugin System**: Extensible tool integration
- [ ] **Audit Logging**: Comprehensive audit trails

### Scalability Improvements

- [ ] **Database Optimization**: Connection pooling and query optimization
- [ ] **Caching Enhancement**: Advanced caching strategies
- [ ] **Load Balancing**: Horizontal scaling support
- [ ] **Microservices**: Service decomposition
- [ ] **Event Streaming**: Kafka/RabbitMQ integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [FastMCP](https://github.com/fastmcp/fastmcp) for MCP protocol implementation
- [JWT](https://jwt.io/) for authentication
- [Prometheus](https://prometheus.io/) for monitoring
- [OpenTelemetry](https://opentelemetry.io/) for distributed tracing
- [Docker](https://www.docker.com/) for containerization

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/metamcp/metamcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/metamcp/metamcp/discussions)
- **Email**: support@metamcp.org

---

**MetaMCP** - Empowering tool orchestration and workflow composition for the Model Context Protocol ecosystem.