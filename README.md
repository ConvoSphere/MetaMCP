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
- **Comprehensive Testing**: Unit tests, integration tests, and performance tests with high coverage

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

# Run tests
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
                    "input_data": "$fetch_data.result",
                    "processing_type": "aggregation"
                }
            },
            "depends_on": ["fetch_data"]
        },
        {
            "id": "save_results",
            "name": "Save Results",
            "step_type": "tool_call",
            "config": {
                "tool_name": "file_operations",
                "arguments": {
                    "operation": "write",
                    "path": "/results/output.json",
                    "content": "$process_data.result"
                }
            },
            "depends_on": ["process_data"]
        }
    ],
    "entry_point": "fetch_data",
    "parallel_execution": false,
    "timeout": 300
}

response = requests.post(
    "http://localhost:8000/api/v1/composition/workflows",
    json={"workflow": workflow_definition},
    headers={"Authorization": f"Bearer {token}"}
)

# Execute a workflow
execution_request = {
    "workflow_id": "data-processing-workflow",
    "input_data": {"database_name": "production_db"},
    "variables": {"environment": "production"},
    "timeout": 600
}

response = requests.post(
    "http://localhost:8000/api/v1/composition/workflows/data-processing-workflow/execute",
    json=execution_request,
    headers={"Authorization": f"Bearer {token}"}
)

# Check execution status
response = requests.get(
    "http://localhost:8000/api/v1/composition/executions/{execution_id}",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Search Tools

```python
# Search tools
response = requests.get(
    "http://localhost:8000/api/v1/tools/search",
    params={
        "q": "database query",
        "search_type": "hybrid",
        "max_results": 10,
        "similarity_threshold": 0.7
    },
    headers={"Authorization": f"Bearer {token}"}
)
```

### Health Monitoring

```bash
# Basic health check
curl "http://localhost:8000/api/v1/health"

# Detailed health status
curl "http://localhost:8000/api/v1/health/detailed"

# Kubernetes probes
curl "http://localhost:8000/api/v1/health/ready"
curl "http://localhost:8000/api/v1/health/live"
```

## 🔄 Workflow Composition Features

### Step Types

MetaMCP supports various step types for complex workflow orchestration:

- **Tool Calls**: Execute tools with variable substitution
- **Conditions**: Evaluate conditions and branch accordingly
- **Parallel Steps**: Execute multiple sub-steps concurrently
- **Loops**: Iterate over collections with loop variables
- **Delays**: Add delays between steps
- **HTTP Requests**: Make HTTP requests with dynamic data

### Variable Management

- **Variable Substitution**: Replace variables in step configurations
- **State Persistence**: Maintain workflow state across steps
- **Loop Variables**: Automatic loop variable management
- **Dynamic Values**: Runtime variable evaluation

### Error Handling

- **Retry Logic**: Configurable retry with exponential backoff
- **Error Recovery**: Graceful error handling and recovery
- **Circuit Breaker**: Integration with existing circuit breaker patterns
- **Timeout Management**: Configurable timeouts for all operations

### Example Workflow

```json
{
  "id": "ml-pipeline",
  "name": "Machine Learning Pipeline",
  "description": "Complete ML data processing pipeline",
  "steps": [
    {
      "id": "data_extraction",
      "name": "Extract Data",
      "step_type": "tool_call",
      "config": {
        "tool_name": "data_extractor",
        "arguments": {
          "source": "$data_source",
          "format": "csv"
        }
      }
    },
    {
      "id": "data_validation",
      "name": "Validate Data",
      "step_type": "condition",
      "config": {
        "condition": {
          "operator": "greater_than",
          "left_operand": "$data_extraction.record_count",
          "right_operand": 1000
        }
      },
      "depends_on": ["data_extraction"]
    },
    {
      "id": "feature_engineering",
      "name": "Feature Engineering",
      "step_type": "tool_call",
      "config": {
        "tool_name": "feature_engineer",
        "arguments": {
          "input_data": "$data_extraction.result",
          "features": ["numeric", "categorical"]
        }
      },
      "depends_on": ["data_validation"]
    },
    {
      "id": "model_training",
      "name": "Train Model",
      "step_type": "tool_call",
      "config": {
        "tool_name": "ml_trainer",
        "arguments": {
          "features": "$feature_engineering.result",
          "algorithm": "random_forest",
          "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 10
          }
        }
      },
      "depends_on": ["feature_engineering"]
    },
    {
      "id": "model_evaluation",
      "name": "Evaluate Model",
      "step_type": "tool_call",
      "config": {
        "tool_name": "model_evaluator",
        "arguments": {
          "model": "$model_training.result",
          "test_data": "$data_extraction.result"
        }
      },
      "depends_on": ["model_training"]
    }
  ],
  "entry_point": "data_extraction",
  "parallel_execution": false,
  "timeout": 1800
}
```

## 🧪 Testing

MetaMCP includes comprehensive testing with high coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=metamcp --cov-report=html

# Run specific test categories
pytest tests/test_auth.py      # Authentication tests
pytest tests/test_tools.py     # Tool management tests
pytest tests/test_composition.py # Workflow composition tests
pytest tests/test_services.py  # Service layer tests
pytest tests/test_utils.py     # Utility component tests

# Run performance tests
pytest tests/test_performance.py

# Run security tests
pytest tests/test_security.py

# Run black-box tests
pytest tests/blackbox/
```

### Test Categories

- **Unit Tests**: Individual function and class testing
- **Integration Tests**: API endpoint and service interaction testing
- **Workflow Tests**: Workflow composition and execution testing
- **Performance Tests**: Load testing and resource monitoring
- **Security Tests**: Authentication, authorization, and vulnerability testing
- **Black-Box Tests**: Containerized API testing for end-to-end validation

### Code Quality

```bash
# Run linting
flake8 metamcp/
ruff check metamcp/
bandit -r metamcp/

# Run type checking
mypy metamcp/

# Run all quality checks
make lint
make test
make security
```

## 🔧 Configuration

### Environment Variables

```bash
# Server Configuration
META_MCP_HOST=0.0.0.0
META_MCP_PORT=8000
META_MCP_DEBUG=false

# Security Configuration
META_MCP_SECRET_KEY=your-secret-key
META_MCP_ALGORITHM=HS256
META_MCP_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Configuration
META_MCP_DATABASE_URL=postgresql://user:pass@localhost/meta_mcp

# Cache Configuration
META_MCP_REDIS_URL=redis://localhost:6379
META_MCP_CACHE_TTL=300

# Monitoring Configuration
META_MCP_METRICS_ENABLED=true
META_MCP_LOGGING_LEVEL=INFO
META_MCP_TELEMETRY_ENABLED=true

# Workflow Configuration
META_MCP_WORKFLOW_TIMEOUT=3600
META_MCP_WORKFLOW_MAX_RETRIES=3
META_MCP_WORKFLOW_PARALLEL_LIMIT=10
```

### Circuit Breaker Configuration

```python
from metamcp.utils.circuit_breaker import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=3,      # Number of failures before opening
    recovery_timeout=10.0,    # Time to wait before half-open
    monitor_interval=5.0      # Monitoring interval
)
```

### Cache Configuration

```python
from metamcp.utils.cache import CacheConfig

config = CacheConfig(
    ttl=300,        # Time to live in seconds
    max_size=1000   # Maximum number of cache entries
)
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t metamcp .

# Run container
docker run -d \
  --name metamcp \
  -p 8000:8000 \
  -e META_MCP_SECRET_KEY="your-secret-key" \
  -e META_MCP_REDIS_URL="redis://redis:6379" \
  metamcp
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: metamcp
  template:
    metadata:
      labels:
        app: metamcp
    spec:
      containers:
      - name: metamcp
        image: metamcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: META_MCP_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: metamcp-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
```

### Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
  
  alertmanager:
    image: prom/alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
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
- **Testing**: High test coverage with unit and integration tests
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

- ✅ **Workflow Composition**: Complete workflow orchestration engine
- ✅ **FastMCP 2.0 Integration**: Full compatibility with latest MCP protocol
- ✅ **OpenTelemetry Support**: Distributed tracing and observability
- ✅ **Enhanced Testing**: Comprehensive test suite with black-box testing
- ✅ **Code Quality**: Improved linting and security scanning
- ✅ **Error Handling**: Robust exception handling and error recovery
- ✅ **Health Monitoring**: Comprehensive health checks and metrics

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