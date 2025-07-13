# MetaMCP Architecture Guide

## Overview

MetaMCP is a comprehensive tool management and execution platform that provides a unified interface for discovering, registering, and executing tools across multiple Model Context Protocol (MCP) servers. The architecture follows modern software engineering principles with clear separation of concerns, modular design, and robust error handling.

## System Architecture

### High-Level Architecture

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

## Core Components

### 1. API Layer (`metamcp/api/`)

The API layer provides RESTful endpoints for all MetaMCP operations.

#### Key Components:
- **`router.py`**: Main API router factory and endpoint registration
- **`auth.py`**: Authentication and authorization endpoints
- **`tools.py`**: Tool management and execution endpoints
- **`health.py`**: Health monitoring and system status endpoints
- **`proxy.py`**: Proxy management for MCP servers

#### API Endpoints:
```
/api/v1/
├── auth/
│   ├── login          # User authentication
│   ├── logout         # User logout
│   ├── refresh        # Token refresh
│   ├── me             # Current user info
│   └── permissions    # User permissions
├── tools/
│   ├── /              # List tools
│   ├── /{name}        # Get tool details
│   ├── /{name}/execute # Execute tool
│   └── /search        # Search tools
├── health/
│   ├── /              # Basic health check
│   ├── /detailed      # Detailed health status
│   ├── /ready         # Readiness probe
│   └── /live          # Liveness probe
└── proxy/
    ├── /servers       # List proxy servers
    └── /servers/{id}  # Server details
```

### 2. Service Layer (`metamcp/services/`)

The service layer contains business logic and separates concerns from API controllers.

#### Key Services:

##### ToolService (`tool_service.py`)
- Tool registration and management
- Tool execution with HTTP calls
- Tool search and discovery
- Execution history tracking
- Tool statistics and metrics

##### AuthService (`auth_service.py`)
- User authentication and authorization
- JWT token management
- Permission checking
- User management (CRUD operations)
- Login history tracking

##### SearchService (`search_service.py`)
- Semantic search implementation
- Keyword-based search
- Hybrid search combining multiple strategies
- Search metrics and statistics
- Search history tracking

### 3. Utility Layer (`metamcp/utils/`)

The utility layer provides reusable components and patterns.

#### Key Utilities:

##### Circuit Breaker (`circuit_breaker.py`)
- Three-state circuit breaker pattern (CLOSED, OPEN, HALF_OPEN)
- Failure threshold management
- Automatic recovery mechanisms
- Circuit breaker manager for centralized monitoring
- Decorator pattern for easy integration

##### Caching System (`cache.py`)
- Multiple backend support (Memory, Redis)
- TTL and eviction policies
- Cache decorator for function result caching
- Cache invalidation strategies
- Cache statistics and monitoring

##### Logging (`logging.py`)
- Structured logging configuration
- Log level management
- Log formatting and output
- Performance logging

### 4. MCP Integration (`metamcp/mcp/`)

The MCP layer handles Model Context Protocol communication.

#### Key Components:
- **`server.py`**: MCP server implementation
- Vector search functionality
- Tool discovery and registration
- Protocol message handling

### 5. Proxy Management (`metamcp/proxy/`)

The proxy layer manages connections to external MCP servers.

#### Key Components:
- **`manager.py`**: Proxy server management
- **`wrapper.py`**: Server wrapping functionality
- **`interceptor.py`**: Request/response interception
- **`discovery.py`**: Server discovery mechanisms

## Data Flow

### 1. Tool Registration Flow
```
Client Request → API Router → ToolService → Tool Registry → Response
```

### 2. Tool Execution Flow
```
Client Request → API Router → ToolService → Circuit Breaker → HTTP Client → MCP Server → Response
```

### 3. Authentication Flow
```
Client Request → API Router → AuthService → JWT Validation → Permission Check → Response
```

### 4. Search Flow
```
Client Request → API Router → SearchService → Vector Search → Cache → Response
```

## Security Architecture

### Authentication
- JWT-based authentication
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

## Performance Architecture

### Caching Strategy
- **Memory Cache**: Fast access for frequently used data
- **Redis Cache**: Distributed caching for scalability
- **Cache Decorators**: Automatic function result caching
- **TTL Management**: Automatic cache expiration

### Circuit Breaker Pattern
- **Failure Detection**: Automatic failure threshold monitoring
- **Recovery Mechanisms**: Automatic circuit recovery
- **Fallback Strategies**: Graceful degradation
- **Monitoring**: Real-time circuit breaker statistics

### Health Monitoring
- **Uptime Tracking**: System uptime calculation
- **Component Health**: Individual service health checks
- **Readiness Probes**: Kubernetes readiness checks
- **Liveness Probes**: Kubernetes liveness checks

## Error Handling

### Exception Hierarchy
```
MetaMCPException (Base)
├── AuthenticationError
├── ValidationError
├── ToolNotFoundError
├── ToolExecutionError
├── SearchError
└── CircuitBreakerOpenError
```

### Error Response Format
```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    "field": "additional_error_details"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Configuration Management

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
```

## Deployment Architecture

### Docker Containerization
- **Multi-stage builds** for optimized images
- **Health checks** for container monitoring
- **Resource limits** for stability
- **Security scanning** for vulnerabilities

### Kubernetes Deployment
- **Deployment manifests** for scalability
- **Service definitions** for networking
- **Ingress configuration** for external access
- **ConfigMaps and Secrets** for configuration

### Monitoring Stack
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **AlertManager** for alerting
- **Jaeger** for distributed tracing

## Development Guidelines

### Code Organization
- **Modular design** with clear separation of concerns
- **Service layer** for business logic
- **Utility layer** for reusable components
- **API layer** for HTTP interface

### Testing Strategy
- **Unit tests** for individual components
- **Integration tests** for API endpoints
- **Performance tests** for load testing
- **Security tests** for vulnerability assessment

### Code Quality
- **Type hints** throughout the codebase
- **Comprehensive error handling**
- **Structured logging** for debugging
- **Documentation** for all public APIs

## Future Enhancements

### Planned Features
1. **Rate Limiting**: Per-user and per-endpoint rate limits
2. **API Versioning**: Proper API versioning strategy
3. **Admin UI**: Web-based administration interface
4. **Policy Engine**: OPA-based policy evaluation
5. **Multi-tenancy**: Tenant isolation and management

### Scalability Improvements
1. **Database Optimization**: Connection pooling and query optimization
2. **Caching Enhancement**: Advanced caching strategies
3. **Load Balancing**: Horizontal scaling support
4. **Microservices**: Service decomposition

### Security Enhancements
1. **OAuth2 Integration**: Third-party authentication
2. **Multi-factor Authentication**: Enhanced security
3. **Audit Logging**: Comprehensive audit trails
4. **Encryption**: Data encryption at rest and in transit

## Conclusion

The MetaMCP architecture provides a robust, scalable, and maintainable foundation for tool management and execution. The modular design allows for easy extension and modification, while the comprehensive error handling and monitoring ensure reliable operation in production environments.

The architecture follows modern software engineering principles and is designed to support both current requirements and future growth. The clear separation of concerns, comprehensive testing strategy, and robust error handling make it suitable for enterprise deployment. 