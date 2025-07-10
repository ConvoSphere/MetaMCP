# Code Structure

This document provides an overview of the MetaMCP codebase structure and architecture.

## Project Structure

```
MetaMCP/
├── metamcp/                    # Main Python package
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Application entry point
│   ├── server.py              # Core server implementation
│   ├── config.py              # Configuration management
│   ├── client.py              # Client library
│   ├── exceptions.py          # Custom exception classes
│   ├── api/                   # REST API modules
│   │   ├── __init__.py
│   │   ├── router.py          # Main API router
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── tools.py           # Tool management endpoints
│   │   └── health.py          # Health check endpoints
│   ├── mcp/                   # MCP Protocol implementation
│   │   └── server.py          # FastMCP server handler
│   ├── tools/                 # Tool management
│   │   └── registry.py        # Tool registry
│   ├── vector/                # Vector search
│   │   └── client.py          # Weaviate client
│   ├── llm/                   # LLM integration
│   │   └── service.py         # LLM service
│   ├── security/              # Security modules
│   │   ├── auth.py            # Authentication manager
│   │   └── policies.py        # Policy engine
│   └── utils/                 # Utility modules
│       ├── __init__.py
│       ├── logging.py         # Logging utilities
│       └── helpers.py         # Helper functions
├── policies/                  # OPA policy definitions
│   ├── admin_access.rego      # Admin access policies
│   └── tool_access.rego       # Tool access policies
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker services
├── Dockerfile                 # Docker image
├── requirements.txt           # Python dependencies
├── setup.py                  # Package setup
└── README.md                 # Project overview
```

## Core Components

### 1. Main Application (`metamcp/main.py`)

The main entry point that sets up the FastAPI application:

```python
from metamcp.main import create_app, run_server

# Create FastAPI app
app = create_app()

# Run server
if __name__ == "__main__":
    asyncio.run(run_server())
```

**Key Features:**
- FastAPI application setup
- Middleware configuration
- Exception handlers
- API router inclusion
- Lifespan management

### 2. Core Server (`metamcp/server.py`)

The central orchestrator that manages all components:

```python
class MetaMCPServer:
    def __init__(self):
        self.tool_registry = None
        self.vector_client = None
        self.auth_manager = None
        self.policy_engine = None
        self.mcp_handler = None
        self.llm_service = None
```

**Responsibilities:**
- Component initialization and lifecycle
- Health checks
- Tool search and execution
- Policy enforcement
- Audit logging

### 3. Configuration (`metamcp/config.py`)

Pydantic-based configuration management:

```python
class Settings(BaseSettings):
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database configuration
    database_url: str
    
    # Vector database
    weaviate_url: str = "http://localhost:8088"
    
    # LLM configuration
    llm_provider: LLMProvider = LLMProvider.OPENAI
    openai_api_key: Optional[SecretStr] = None
```

**Features:**
- Environment variable loading
- Type validation
- Default values
- Secret management

### 4. MCP Protocol (`metamcp/mcp/server.py`)

FastMCP 2.10.4 integration for MCP protocol handling:

```python
from fastmcp import FastMCP, MCPRequest, MCPResponse

class MCPServerHandler:
    def __init__(self, tool_registry, auth_manager, policy_engine):
        self.fastmcp = FastMCP(
            name="MetaMCP Server",
            version="1.0.0"
        )
```

**Features:**
- WebSocket connection management
- Protocol message handling
- Tool listing and execution
- Authentication integration

### 5. Tool Registry (`metamcp/tools/registry.py`)

Manages tool registration, discovery, and execution:

```python
class ToolRegistry:
    def __init__(self, vector_client, llm_service, policy_engine):
        self.tools = {}
        self.tool_embeddings = {}
        self.execution_history = []
```

**Features:**
- Tool registration and metadata
- Semantic search
- Access control
- Execution tracking

### 6. Vector Search (`metamcp/vector/client.py`)

Weaviate integration for semantic search:

```python
class VectorSearchClient:
    def __init__(self, url, api_key=None, timeout=30):
        self.client = None
        self.url = url
```

**Features:**
- Embedding storage and retrieval
- Similarity search
- Collection management
- Connection pooling

### 7. LLM Service (`metamcp/llm/service.py`)

Multi-provider LLM integration:

```python
class LLMService:
    def __init__(self, settings):
        self.provider = settings.llm_provider
        self.openai_client = None
        self.ollama_client = None
```

**Supported Providers:**
- OpenAI (GPT models)
- Ollama (local models)
- Hugging Face (transformers)

### 8. Security (`metamcp/security/`)

Authentication and authorization:

```python
class AuthManager:
    def __init__(self, settings):
        self.pwd_context = CryptContext(schemes=["bcrypt"])
        self.users = {}

class PolicyEngine:
    def __init__(self, engine_type, opa_url=None):
        self.engine_type = engine_type
        self.opa_url = opa_url
```

**Features:**
- JWT token management
- Password hashing
- Role-based access control
- OPA policy integration

## API Structure

### REST API (`metamcp/api/`)

FastAPI-based REST endpoints:

```python
# Main router
router = APIRouter()
router.include_router(tools_router, prefix="/tools")
router.include_router(health_router, prefix="/health")
router.include_router(auth_router, prefix="/auth")
```

**Endpoints:**
- `/api/v1/tools` - Tool management
- `/api/v1/health` - Health checks
- `/api/v1/auth` - Authentication

### MCP WebSocket

WebSocket-based MCP protocol:

```python
# WebSocket handler
async def handle_websocket(websocket, path):
    async for message in websocket:
        request = MCPRequest(**json.loads(message))
        response = await fastmcp.handle_request(request)
        await websocket.send(json.dumps(response.dict()))
```

## Modularity Principles

### 1. Dependency Injection

Components receive dependencies through constructor injection:

```python
class MetaMCPServer:
    def __init__(self):
        self.tool_registry = ToolRegistry(
            vector_client=self.vector_client,
            llm_service=self.llm_service,
            policy_engine=self.policy_engine
        )
```

### 2. Interface Segregation

Each module has a clear, focused responsibility:

- **Tool Registry**: Tool management only
- **Vector Client**: Vector operations only
- **Auth Manager**: Authentication only
- **Policy Engine**: Authorization only

### 3. Configuration-Driven

Components are configured through settings:

```python
# Initialize based on configuration
if settings.llm_provider == LLMProvider.OPENAI:
    await self._initialize_openai()
elif settings.llm_provider == LLMProvider.OLLAMA:
    await self._initialize_ollama()
```

### 4. Error Handling

Consistent error handling across modules:

```python
class MetaMCPError(Exception):
    def __init__(self, message, error_code, status_code=500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
```

## Testing Structure

```
tests/
├── unit/                      # Unit tests
│   ├── test_server.py
│   ├── test_tools.py
│   └── test_auth.py
├── integration/               # Integration tests
│   ├── test_api.py
│   └── test_mcp.py
├── e2e/                      # End-to-end tests
│   └── test_workflows.py
└── conftest.py               # Test configuration
```

## Development Guidelines

### 1. Code Style

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### 2. Documentation

- **Docstrings**: All public methods
- **Type Hints**: All function parameters
- **README**: Project overview
- **API Docs**: Auto-generated from FastAPI

### 3. Testing

- **Unit Tests**: Individual components
- **Integration Tests**: Component interactions
- **E2E Tests**: Complete workflows
- **Coverage**: Minimum 80%

### 4. Error Handling

- **Custom Exceptions**: Domain-specific errors
- **Logging**: Structured logging with levels
- **Audit Trail**: Complete request tracking

## Extension Points

### 1. Adding New Tools

```python
# Register a new tool
await tool_registry.register_tool({
    "name": "my_tool",
    "description": "My custom tool",
    "endpoint": "http://my-tool:8000",
    "input_schema": {...}
})
```

### 2. Custom Policies

```rego
# policies/custom.rego
package metamcp.custom

allow {
    input.user.role == "custom_role"
    input.resource == "custom_resource"
}
```

### 3. New LLM Providers

```python
# Add new provider to LLMService
async def _initialize_custom_provider(self):
    # Custom initialization logic
    pass
```

This modular structure ensures maintainability, testability, and extensibility while providing clear separation of concerns. 