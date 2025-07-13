# MetaMCP API Reference

## Overview

The MetaMCP API provides a comprehensive RESTful interface for tool management, execution, and system administration. The API follows REST principles and uses JSON for data exchange.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Error Response
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

## Authentication Endpoints

### POST /auth/login

Authenticate a user and receive an access token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "user_id": "admin_user",
      "username": "admin",
      "roles": ["admin"],
      "permissions": {
        "tools": ["read", "write", "execute"],
        "admin": ["manage", "configure"]
      }
    }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### POST /auth/logout

Logout the current user and invalidate the token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "message": "Successfully logged out"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### POST /auth/refresh

Refresh an expired access token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /auth/me

Get current user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "admin_user",
    "username": "admin",
    "roles": ["admin"],
    "permissions": {
      "tools": ["read", "write", "execute"],
      "admin": ["manage", "configure"]
    },
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /auth/permissions

Get current user permissions.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "admin_user",
    "username": "admin",
    "roles": ["admin"],
    "permissions": {
      "tools": ["read", "write", "execute"],
      "admin": ["manage", "configure"]
    }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Tool Management Endpoints

### GET /tools

List all available tools with optional filtering.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `category` (optional): Filter by tool category
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "status": "success",
  "data": {
    "tools": [
      {
        "name": "database_query",
        "description": "Execute SQL queries on database",
        "category": "database",
        "endpoint": "http://localhost:8001",
        "capabilities": ["read", "write"],
        "security_level": 2,
        "version": "1.0.0",
        "author": "MetaMCP Team",
        "tags": ["database", "sql"],
        "is_active": true,
        "created_at": "2023-01-01T00:00:00Z",
        "created_by": "admin_user"
      }
    ],
    "total": 1,
    "offset": 0,
    "limit": 50
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /tools/{name}

Get detailed information about a specific tool.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "name": "database_query",
    "description": "Execute SQL queries on database",
    "category": "database",
    "endpoint": "http://localhost:8001",
    "capabilities": ["read", "write"],
    "security_level": 2,
    "schema": {
      "input": {
        "query": {
          "type": "string",
          "description": "SQL query to execute"
        }
      },
      "output": {
        "result": {
          "type": "array",
          "description": "Query results"
        }
      }
    },
    "metadata": {
      "version": "1.0.0",
      "author": "MetaMCP Team"
    },
    "version": "1.0.0",
    "author": "MetaMCP Team",
    "tags": ["database", "sql"],
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "created_by": "admin_user"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### POST /tools

Register a new tool.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "new_tool",
  "description": "A new tool for testing",
  "endpoint": "http://localhost:8002",
  "category": "api",
  "capabilities": ["read"],
  "security_level": 1,
  "schema": {
    "input": {},
    "output": {}
  },
  "metadata": {
    "version": "1.0.0"
  },
  "version": "1.0.0",
  "author": "test_author",
  "tags": ["test", "api"]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "tool_id": "tool_123456789",
    "message": "Tool registered successfully"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### PUT /tools/{name}

Update an existing tool.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "description": "Updated description",
  "category": "updated_category",
  "capabilities": ["read", "write", "execute"],
  "security_level": 3
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "name": "new_tool",
    "description": "Updated description",
    "category": "updated_category",
    "capabilities": ["read", "write", "execute"],
    "security_level": 3,
    "updated_at": "2023-01-01T00:00:00Z",
    "updated_by": "admin_user"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### DELETE /tools/{name}

Deactivate a tool (soft delete).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "message": "Tool deactivated successfully"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### POST /tools/{name}/execute

Execute a tool with given arguments.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "arguments": {
    "query": "SELECT * FROM users LIMIT 10",
    "database": "test_db"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "tool_name": "database_query",
    "input_data": {
      "query": "SELECT * FROM users LIMIT 10",
      "database": "test_db"
    },
    "output_data": {
      "result": [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"}
      ]
    },
    "status": "success",
    "execution_time": 0.125,
    "executed_by": "admin_user",
    "timestamp": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /tools/search

Search tools by query string.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `q` (required): Search query
- `max_results` (optional): Maximum number of results (default: 10)
- `similarity_threshold` (optional): Minimum similarity score (default: 0.5)
- `search_type` (optional): Search type - "semantic", "keyword", or "hybrid" (default: "hybrid")

**Response:**
```json
{
  "status": "success",
  "data": {
    "search_id": "search_123456789",
    "query": "database query",
    "search_type": "hybrid",
    "results": [
      {
        "name": "database_query",
        "description": "Execute SQL queries on database",
        "category": "database",
        "similarity_score": 0.85,
        "tags": ["database", "sql"]
      }
    ],
    "total": 1,
    "search_time": 0.045,
    "timestamp": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Health Monitoring Endpoints

### GET /health

Basic health check endpoint.

**Response:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /health/detailed

Detailed health status with component information.

**Response:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "uptime": 3600.5,
    "version": "1.0.0",
    "components": {
      "database": {
        "status": "healthy",
        "response_time": 0.002
      },
      "cache": {
        "status": "healthy",
        "hit_rate": 0.85
      },
      "circuit_breakers": {
        "status": "healthy",
        "open_circuits": 0,
        "total_circuits": 5
      }
    },
    "timestamp": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /health/ready

Kubernetes readiness probe endpoint.

**Response:**
```json
{
  "status": "success",
  "data": {
    "ready": true,
    "timestamp": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /health/live

Kubernetes liveness probe endpoint.

**Response:**
```json
{
  "status": "success",
  "data": {
    "alive": true,
    "timestamp": "2023-01-01T00:00:00Z"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Proxy Management Endpoints

### GET /proxy/servers

List all proxy servers.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "servers": [
      {
        "id": "server_1",
        "name": "Database Server",
        "endpoint": "http://localhost:8001",
        "status": "active",
        "tool_count": 5,
        "last_seen": "2023-01-01T00:00:00Z",
        "metadata": {
          "version": "1.0.0",
          "description": "Database tools server"
        }
      }
    ],
    "total": 1
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### GET /proxy/servers/{id}

Get detailed information about a specific proxy server.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "server_1",
    "name": "Database Server",
    "endpoint": "http://localhost:8001",
    "status": "active",
    "tool_count": 5,
    "last_seen": "2023-01-01T00:00:00Z",
    "metadata": {
      "version": "1.0.0",
      "description": "Database tools server"
    },
    "tools": [
      {
        "name": "database_query",
        "description": "Execute SQL queries",
        "category": "database"
      }
    ],
    "statistics": {
      "total_requests": 150,
      "successful_requests": 145,
      "failed_requests": 5,
      "average_response_time": 0.125
    }
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTHENTICATION_ERROR` | Invalid or missing authentication token |
| `AUTHORIZATION_ERROR` | Insufficient permissions for the requested operation |
| `VALIDATION_ERROR` | Invalid request data or missing required fields |
| `TOOL_NOT_FOUND` | Requested tool does not exist |
| `TOOL_EXECUTION_ERROR` | Error occurred during tool execution |
| `CIRCUIT_BREAKER_OPEN` | Circuit breaker is open, request rejected |
| `SEARCH_ERROR` | Error occurred during search operation |
| `INTERNAL_ERROR` | Internal server error |

## Rate Limiting

Rate limiting is planned for future releases. Limits will be applied per user and per endpoint.

## API Versioning

The API uses URL-based versioning (`/api/v1/`). Future versions will be available at `/api/v2/`, etc.

## SDKs and Libraries

Official SDKs and libraries are planned for:
- Python
- JavaScript/TypeScript
- Go
- Java

## Support

For API support and questions, please refer to the project documentation or create an issue in the GitHub repository. 