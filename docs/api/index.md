# API Documentation

MetaMCP provides a comprehensive REST API for tool discovery, execution, and management.

## Overview

The MetaMCP API is built on FastAPI and provides:

- **Tool Management**: Register, discover, and execute tools
- **Vector Search**: Semantic search for tools
- **Authentication**: JWT-based authentication
- **Monitoring**: Built-in metrics and health checks
- **MCP Protocol**: WebSocket support for MCP clients

## Base URL

```
http://localhost:8000
```

## Authentication

### JWT Authentication

Most endpoints require authentication using JWT tokens.

```bash
# Get token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Use token
curl -X GET "http://localhost:8000/api/tools" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### API Key Authentication

For service-to-service communication:

```bash
curl -X GET "http://localhost:8000/api/tools" \
  -H "X-API-Key: YOUR_API_KEY"
```

## Endpoints

### Health Check

#### GET /health

Check service health status.

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "vector_search": "healthy",
    "llm_service": "healthy"
  }
}
```

### Authentication

#### POST /auth/login

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

#### POST /auth/refresh

Refresh JWT token.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Tools

#### GET /api/tools

List all available tools.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**
- `limit` (int): Maximum number of tools to return (default: 100)
- `offset` (int): Number of tools to skip (default: 0)
- `category` (str): Filter by tool category
- `tags` (str): Filter by tags (comma-separated)

**Response:**
```json
{
  "tools": [
    {
      "id": "calculator",
      "name": "Calculator",
      "description": "Perform mathematical calculations",
      "version": "1.0.0",
      "categories": ["math", "calculation"],
      "tags": ["calculator", "math"],
      "input_schema": {
        "type": "object",
        "properties": {
          "operation": {
            "type": "string",
            "enum": ["add", "subtract", "multiply", "divide"]
          },
          "a": {"type": "number"},
          "b": {"type": "number"}
        },
        "required": ["operation", "a", "b"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "result": {"type": "number"}
        }
      },
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/tools/{tool_id}

Get specific tool details.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
  "id": "calculator",
  "name": "Calculator",
  "description": "Perform mathematical calculations",
  "version": "1.0.0",
  "categories": ["math", "calculation"],
  "tags": ["calculator", "math"],
  "input_schema": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "enum": ["add", "subtract", "multiply", "divide"]
      },
      "a": {"type": "number"},
      "b": {"type": "number"}
    },
    "required": ["operation", "a", "b"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "result": {"type": "number"}
    }
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### POST /api/tools/{tool_id}/execute

Execute a tool.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "input": {
    "operation": "add",
    "a": 5,
    "b": 3
  }
}
```

**Response:**
```json
{
  "result": {
    "result": 8
  },
  "execution_time": 0.123,
  "success": true,
  "tool_id": "calculator"
}
```

#### POST /api/tools

Register a new tool.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "name": "New Tool",
  "description": "A new tool description",
  "version": "1.0.0",
  "categories": ["utility"],
  "tags": ["new", "tool"],
  "input_schema": {
    "type": "object",
    "properties": {
      "input": {"type": "string"}
    },
    "required": ["input"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "output": {"type": "string"}
    }
  }
}
```

**Response:**
```json
{
  "id": "new_tool_123",
  "name": "New Tool",
  "description": "A new tool description",
  "version": "1.0.0",
  "categories": ["utility"],
  "tags": ["new", "tool"],
  "input_schema": {
    "type": "object",
    "properties": {
      "input": {"type": "string"}
    },
    "required": ["input"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "output": {"type": "string"}
    }
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Vector Search

#### POST /api/search

Search for tools using semantic search.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "query": "mathematical calculation tool",
  "limit": 10,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "results": [
    {
      "tool_id": "calculator",
      "name": "Calculator",
      "description": "Perform mathematical calculations",
      "similarity_score": 0.95,
      "categories": ["math", "calculation"],
      "tags": ["calculator", "math"]
    }
  ],
  "total_results": 1,
  "query": "mathematical calculation tool",
  "search_time": 0.123
}
```

### MCP Protocol

#### WebSocket /mcp/ws

Connect to MCP protocol over WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/mcp/ws');

ws.onopen = function() {
  console.log('Connected to MCP');
};

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

**MCP Messages:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### Monitoring

#### GET /metrics

Get Prometheus metrics.

**Response:**
```
# HELP metamcp_requests_total Total number of requests
# TYPE metamcp_requests_total counter
metamcp_requests_total{method="GET",path="/api/tools",status_code="200"} 42

# HELP metamcp_request_duration_seconds Request duration in seconds
# TYPE metamcp_request_duration_seconds histogram
metamcp_request_duration_seconds_bucket{method="GET",path="/api/tools",le="0.1"} 35
metamcp_request_duration_seconds_bucket{method="GET",path="/api/tools",le="0.5"} 40
metamcp_request_duration_seconds_bucket{method="GET",path="/api/tools",le="1.0"} 42
```

## Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    "field": "additional_error_details"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `authentication_failed` | Invalid credentials | 401 |
| `authorization_failed` | Insufficient permissions | 403 |
| `tool_not_found` | Tool does not exist | 404 |
| `tool_execution_failed` | Tool execution error | 500 |
| `validation_error` | Invalid input data | 400 |
| `rate_limit_exceeded` | Too many requests | 429 |
| `internal_server_error` | Server error | 500 |

### Example Error Response

```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "field": "operation",
    "message": "Operation must be one of: add, subtract, multiply, divide"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

API requests are rate limited to prevent abuse.

### Rate Limits

- **Authentication**: 5 requests per minute
- **Tool Execution**: 100 requests per minute
- **Search**: 50 requests per minute
- **General**: 1000 requests per hour

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters.

### Pagination Headers

```
X-Total-Count: 1000
X-Page-Size: 100
X-Page-Number: 1
```

## SDKs and Libraries

### Python SDK

```python
from metamcp import MetaMCPClient

client = MetaMCPClient("http://localhost:8000", api_key="your_key")

# List tools
tools = client.list_tools()

# Execute tool
result = client.execute_tool("calculator", {
    "operation": "add",
    "a": 5,
    "b": 3
})

# Search tools
results = client.search_tools("mathematical calculation")
```

### JavaScript SDK

```javascript
import { MetaMCPClient } from '@metamcp/client';

const client = new MetaMCPClient('http://localhost:8000', {
  apiKey: 'your_key'
});

// List tools
const tools = await client.listTools();

// Execute tool
const result = await client.executeTool('calculator', {
  operation: 'add',
  a: 5,
  b: 3
});

// Search tools
const results = await client.searchTools('mathematical calculation');
```

## Webhooks

### Webhook Configuration

```json
{
  "url": "https://your-app.com/webhooks/metamcp",
  "events": ["tool.executed", "tool.registered"],
  "secret": "webhook_secret"
}
```

### Webhook Payload

```json
{
  "event": "tool.executed",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "tool_id": "calculator",
    "user_id": "user_123",
    "input": {"operation": "add", "a": 5, "b": 3},
    "result": {"result": 8},
    "execution_time": 0.123
  }
}
```

## OpenAPI Specification

The complete OpenAPI specification is available at:

```
http://localhost:8000/docs
```

This provides interactive documentation and allows you to test the API directly from your browser. 