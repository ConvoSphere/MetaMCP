# API Reference

MetaMCP provides a comprehensive REST API for tool management, authentication, MCP protocol integration, and proxy wrapper functionality.

## Base URL

```
http://localhost:8000
```

## Authentication

Most API endpoints require authentication. Use JWT tokens or OAuth:

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/tools
```

## Endpoints

### Proxy Wrapper

The proxy wrapper provides endpoints for managing wrapped MCP servers. For detailed documentation, see [Proxy API Reference](../reference/proxy-api.md).

#### POST /proxy/servers

Register a new MCP server for wrapping.

#### GET /proxy/servers

List all registered servers.

#### GET /proxy/servers/{server_id}

Get server information.

#### PUT /proxy/servers/{server_id}

Update server configuration.

#### DELETE /proxy/servers/{server_id}

Unregister a server.

#### GET /proxy/health

Check health of all registered servers.

#### POST /proxy/discovery

Discover MCP servers on the network.

#### GET /proxy/tools

List all tools from wrapped servers.

#### POST /proxy/tools/{tool_name}

Execute a tool on a wrapped server.

### Health Check

#### GET /health

Check server health and status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-07-10T19:30:00Z",
  "components": {
    "database": "healthy",
    "vector_search": "healthy",
    "llm_service": "healthy",
    "policy_engine": "healthy"
  }
}
```

### Authentication

#### POST /api/auth/login

Authenticate user and get JWT token.

**Request:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/auth/refresh

Refresh JWT token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/auth/logout

Logout user and invalidate token.

**Request:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### OAuth Authentication

#### GET /api/oauth/login/{provider}

Initiate OAuth login flow.

**Parameters:**
- `provider`: `google`, `github`, or `microsoft`

**Response:** Redirects to OAuth provider

#### GET /api/oauth/callback/{provider}

OAuth callback endpoint.

**Parameters:**
- `provider`: `google`, `github`, or `microsoft`

**Response:** JWT token or error

### Tool Management

#### GET /api/tools

List all available tools.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `limit`: Maximum number of results (default: 50)
- `offset`: Pagination offset (default: 0)
- `category`: Filter by category
- `status`: Filter by status (`active`, `inactive`)

**Response:**
```json
{
  "tools": [
    {
      "id": "calculator-abc123",
      "name": "calculator",
      "description": "Perform mathematical calculations",
      "endpoint": "http://localhost:8001",
      "categories": ["math", "calculation"],
      "status": "active",
      "registered_at": "2025-07-10T19:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/tools

Register a new tool.

**Headers:**
- `Authorization: Bearer <token>` (required)
- `Content-Type: application/json`

**Request:**
```json
{
  "name": "calculator",
  "description": "Perform mathematical calculations",
  "endpoint": "http://localhost:8001",
  "categories": ["math", "calculation"],
  "input_schema": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "description": "Mathematical expression to evaluate"
      }
    },
    "required": ["expression"]
  },
  "security_level": 1
}
```

**Response:**
```json
{
  "id": "calculator-abc123",
  "name": "calculator",
  "status": "active",
  "registered_at": "2025-07-10T19:30:00Z"
}
```

#### GET /api/tools/{tool_id}

Get tool details.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "id": "calculator-abc123",
  "name": "calculator",
  "description": "Perform mathematical calculations",
  "endpoint": "http://localhost:8001",
  "categories": ["math", "calculation"],
  "input_schema": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "description": "Mathematical expression to evaluate"
      }
    },
    "required": ["expression"]
  },
  "status": "active",
  "registered_at": "2025-07-10T19:30:00Z",
  "execution_count": 42,
  "last_executed": "2025-07-10T19:25:00Z"
}
```

#### PUT /api/tools/{tool_id}

Update tool configuration.

**Headers:**
- `Authorization: Bearer <token>` (required)
- `Content-Type: application/json`

**Request:**
```json
{
  "description": "Updated description",
  "categories": ["math", "calculation", "arithmetic"],
  "status": "active"
}
```

#### DELETE /api/tools/{tool_id}

Deactivate a tool.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "message": "Tool deactivated successfully",
  "tool_id": "calculator-abc123"
}
```

### Tool Search

#### POST /api/tools/search

Search tools using semantic search.

**Headers:**
- `Authorization: Bearer <token>` (required)
- `Content-Type: application/json`

**Request:**
```json
{
  "query": "mathematical calculations",
  "max_results": 10,
  "similarity_threshold": 0.7,
  "categories": ["math"]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "calculator-abc123",
      "name": "calculator",
      "description": "Perform mathematical calculations",
      "similarity_score": 0.95,
      "categories": ["math", "calculation"],
      "endpoint": "http://localhost:8001"
    }
  ],
  "total": 1,
  "query": "mathematical calculations"
}
```

### Tool Execution

#### POST /api/tools/{tool_id}/execute

Execute a tool.

**Headers:**
- `Authorization: Bearer <token>` (required)
- `Content-Type: application/json`

**Request:**
```json
{
  "arguments": {
    "expression": "2 + 2 * 3"
  },
  "timeout": 30
}
```

**Response:**
```json
{
  "result": {
    "value": 8,
    "expression": "2 + 2 * 3"
  },
  "execution_time": 0.15,
  "status": "success",
  "tool_id": "calculator-abc123"
}
```

### User Management

#### GET /api/users/me

Get current user information.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "id": "user123",
  "username": "john_doe",
  "email": "john@example.com",
  "roles": ["user"],
  "permissions": ["tool:read", "tool:execute"],
  "created_at": "2025-07-01T10:00:00Z"
}
```

#### GET /api/users/{user_id}

Get user information (admin only).

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "id": "user123",
  "username": "john_doe",
  "email": "john@example.com",
  "roles": ["user"],
  "status": "active",
  "created_at": "2025-07-01T10:00:00Z",
  "last_login": "2025-07-10T19:30:00Z"
}
```

### Policy Management

#### GET /api/policies

List available policies.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "policies": [
    {
      "name": "tool_access",
      "description": "Tool access control policy",
      "version": "1.0.0",
      "enabled": true
    }
  ]
}
```

#### POST /api/policies/evaluate

Evaluate a policy.

**Headers:**
- `Authorization: Bearer <token>` (required)
- `Content-Type: application/json`

**Request:**
```json
{
  "policy_name": "tool_access",
  "input": {
    "user_id": "user123",
    "resource": "tool:calculator",
    "action": "execute"
  }
}
```

**Response:**
```json
{
  "allowed": true,
  "reason": "User has execute permission for this tool",
  "policy_name": "tool_access"
}
```

### Monitoring & Metrics

#### GET /api/metrics

Get system metrics.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Response:**
```json
{
  "requests_total": 1250,
  "requests_per_minute": 15.5,
  "active_connections": 8,
  "memory_usage_mb": 256.5,
  "cpu_usage_percent": 12.3,
  "uptime_seconds": 86400
}
```

#### GET /api/logs

Get system logs.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `level`: Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `limit`: Maximum number of log entries (default: 100)
- `since`: ISO timestamp for filtering

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-07-10T19:30:00Z",
      "level": "INFO",
      "message": "Tool executed successfully",
      "tool_id": "calculator-abc123",
      "user_id": "user123",
      "execution_time": 0.15
    }
  ],
  "total": 1
}
```

## Error Responses

All endpoints may return error responses with the following format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request parameters",
    "details": {
      "field": "name",
      "reason": "Field is required"
    }
  },
  "timestamp": "2025-07-10T19:30:00Z",
  "request_id": "req-123456"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `validation_error` | Invalid request parameters | 400 |
| `authentication_failed` | Invalid credentials | 401 |
| `authorization_failed` | Insufficient permissions | 403 |
| `tool_not_found` | Tool does not exist | 404 |
| `tool_execution_failed` | Tool execution error | 500 |
| `service_unavailable` | Service temporarily unavailable | 503 |

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Authenticated users**: 100 requests per minute
- **Anonymous users**: 10 requests per minute
- **Admin users**: 1000 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```bash
# Get first 10 tools
GET /api/tools?limit=10&offset=0

# Get next 10 tools
GET /api/tools?limit=10&offset=10
```

Pagination metadata is included in responses:

```json
{
  "data": [...],
  "pagination": {
    "total": 50,
    "limit": 10,
    "offset": 0,
    "has_next": true,
    "has_prev": false
  }
}
```

## SDKs and Libraries

### Python

```python
from metamcp.client import MetaMCPClient

client = MetaMCPClient("http://localhost:8000", token="your-token")

# Search tools
tools = await client.search_tools("calculator")

# Execute tool
result = await client.execute_tool("calculator-abc123", {
    "expression": "2 + 2"
})
```

### JavaScript/TypeScript

```javascript
import { MetaMCPClient } from '@metamcp/client';

const client = new MetaMCPClient('http://localhost:8000', {
  token: 'your-token'
});

// Search tools
const tools = await client.searchTools('calculator');

// Execute tool
const result = await client.executeTool('calculator-abc123', {
  expression: '2 + 2'
});
```

## WebSocket API

For real-time updates, MetaMCP also provides a WebSocket API:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Tool execution update:', data);
};
```

WebSocket events include:
- `tool.executed`: Tool execution completed
- `tool.registered`: New tool registered
- `user.authenticated`: User logged in
- `system.health`: Health status update 