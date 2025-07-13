# Proxy API Reference

This document provides detailed API reference for the MetaMCP Proxy Wrapper REST endpoints.

## Base URL

All proxy API endpoints are prefixed with `/proxy`:

```
http://localhost:8000/proxy
```

## Authentication

Most endpoints require authentication. Include your API token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" http://localhost:8000/proxy/servers
```

## Response Format

All API responses follow a consistent format:

### Success Response

```json
{
  "data": {...},
  "message": "Success message",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {...}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Server Management

### Register Server

Register a new MCP server for wrapping.

**Endpoint:** `POST /proxy/servers`

**Request Body:**

```json
{
  "name": "string",
  "endpoint": "string",
  "transport": "string",
  "auth_required": "boolean",
  "auth_token": "string",
  "timeout": "integer",
  "retry_attempts": "integer",
  "security_level": "string",
  "categories": ["string"],
  "description": "string",
  "metadata": {}
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Server name |
| `endpoint` | string | Yes | - | Server endpoint URL |
| `transport` | string | No | "http" | Transport protocol (http, websocket, stdio) |
| `auth_required` | boolean | No | false | Whether authentication is required |
| `auth_token` | string | No | null | Authentication token |
| `timeout` | integer | No | 30 | Request timeout in seconds |
| `retry_attempts` | integer | No | 3 | Number of retry attempts |
| `security_level` | string | No | "medium" | Security level (low, medium, high) |
| `categories` | array | No | [] | Tool categories |
| `description` | string | No | "" | Server description |
| `metadata` | object | No | {} | Additional metadata |

**Response:**

```json
{
  "data": {
    "server_id": "my-server_0"
  },
  "message": "Server registered successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/proxy/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "name": "file-server",
    "endpoint": "http://localhost:8001",
    "transport": "http",
    "auth_required": false,
    "timeout": 30,
    "retry_attempts": 3,
    "security_level": "medium",
    "categories": ["file-operations"],
    "description": "File operations server"
  }'
```

### List Servers

Get a list of all registered servers.

**Endpoint:** `GET /proxy/servers`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status (healthy, unhealthy, unknown) |
| `transport` | string | No | Filter by transport type |
| `category` | string | No | Filter by category |

**Response:**

```json
{
  "data": [
    {
      "server_id": "file-server_0",
      "name": "file-server",
      "endpoint": "http://localhost:8001",
      "transport": "http",
      "status": "healthy",
      "last_seen": "2024-01-15T10:30:00Z",
      "tool_count": 5,
      "categories": ["file-operations"],
      "security_level": "medium"
    }
  ],
  "message": "Servers retrieved successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:8000/proxy/servers?status=healthy"
```

### Get Server Info

Get detailed information about a specific server.

**Endpoint:** `GET /proxy/servers/{server_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `server_id` | string | Yes | Server ID |

**Response:**

```json
{
  "data": {
    "server_id": "file-server_0",
    "name": "file-server",
    "endpoint": "http://localhost:8001",
    "transport": "http",
    "status": "healthy",
    "last_seen": "2024-01-15T10:30:00Z",
    "tool_count": 5,
    "categories": ["file-operations"],
    "security_level": "medium",
    "auth_required": false,
    "timeout": 30,
    "retry_attempts": 3,
    "description": "File operations server",
    "metadata": {
      "version": "1.0.0"
    }
  },
  "message": "Server information retrieved",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:8000/proxy/servers/file-server_0"
```

### Update Server

Update server configuration.

**Endpoint:** `PUT /proxy/servers/{server_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `server_id` | string | Yes | Server ID |

**Request Body:** Same as Register Server

**Response:**

```json
{
  "data": {
    "server_id": "file-server_0"
  },
  "message": "Server updated successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X PUT http://localhost:8000/proxy/servers/file-server_0 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "name": "file-server",
    "endpoint": "http://localhost:8001",
    "transport": "http",
    "timeout": 60,
    "categories": ["file-operations", "data-processing"]
  }'
```

### Unregister Server

Remove a server from the proxy wrapper.

**Endpoint:** `DELETE /proxy/servers/{server_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `server_id` | string | Yes | Server ID |

**Response:**

```json
{
  "data": {
    "server_id": "file-server_0"
  },
  "message": "Server unregistered successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/proxy/servers/file-server_0 \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

## Health Monitoring

### Health Check

Get health status of all registered servers.

**Endpoint:** `GET /proxy/health`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `server_id` | string | No | Check specific server only |

**Response:**

```json
{
  "data": {
    "file-server_0": {
      "server_id": "file-server_0",
      "status": "healthy",
      "last_seen": "2024-01-15T10:30:00Z",
      "healthy": true,
      "error": null,
      "response_time": 0.125,
      "uptime": 3600
    },
    "data-server_1": {
      "server_id": "data-server_1",
      "status": "unhealthy",
      "last_seen": "2024-01-15T10:25:00Z",
      "healthy": false,
      "error": "Connection timeout",
      "response_time": null,
      "uptime": 0
    }
  },
  "message": "Health check completed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:8000/proxy/health?server_id=file-server_0"
```

### Force Health Check

Force a health check for all servers or a specific server.

**Endpoint:** `POST /proxy/health`

**Request Body:**

```json
{
  "server_id": "string"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `server_id` | string | No | Force check for specific server |

**Response:**

```json
{
  "data": {
    "checked_servers": 2,
    "healthy_servers": 1,
    "unhealthy_servers": 1
  },
  "message": "Health check completed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/proxy/health \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"server_id": "file-server_0"}'
```

## Server Discovery

### Discover Servers

Discover MCP servers on the network.

**Endpoint:** `POST /proxy/discovery`

**Request Body:**

```json
{
  "network_discovery": "boolean",
  "service_discovery": "boolean",
  "file_discovery": "boolean",
  "ports": ["integer"],
  "base_urls": ["string"],
  "config_paths": ["string"],
  "service_endpoints": ["string"],
  "timeout": "integer",
  "max_concurrent": "integer"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `network_discovery` | boolean | No | true | Enable network discovery |
| `service_discovery` | boolean | No | false | Enable service discovery |
| `file_discovery` | boolean | No | true | Enable file discovery |
| `ports` | array | No | [8001, 8002, 8003, 8004, 8005] | Ports to scan |
| `base_urls` | array | No | ["http://localhost", "http://127.0.0.1"] | Base URLs to scan |
| `config_paths` | array | No | ["./mcp-servers.json", "./config/mcp-servers.json"] | Config file paths |
| `service_endpoints` | array | No | [] | Service discovery endpoints |
| `timeout` | integer | No | 5 | Discovery timeout |
| `max_concurrent` | integer | No | 10 | Maximum concurrent scans |

**Response:**

```json
{
  "data": {
    "discovered_count": 3,
    "servers": [
      {
        "name": "file-server",
        "endpoint": "http://localhost:8001",
        "transport": "http",
        "status": "discovered",
        "tools": [
          {
            "name": "read_file",
            "description": "Read file contents",
            "input_schema": {...}
          }
        ]
      }
    ],
    "auto_registered": 2,
    "failed_discoveries": 1
  },
  "message": "Discovery completed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/proxy/discovery \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "network_discovery": true,
    "ports": [8001, 8002, 8003],
    "base_urls": ["http://localhost", "http://127.0.0.1"],
    "timeout": 5
  }'
```

### Get Discovered Servers

Get list of discovered servers.

**Endpoint:** `GET /proxy/discovery/servers`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status (discovered, registered, failed) |

**Response:**

```json
{
  "data": [
    {
      "name": "file-server",
      "endpoint": "http://localhost:8001",
      "transport": "http",
      "status": "discovered",
      "discovered_at": "2024-01-15T10:30:00Z",
      "tools": [
        {
          "name": "read_file",
          "description": "Read file contents"
        }
      ]
    }
  ],
  "message": "Discovered servers retrieved",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:8000/proxy/discovery/servers?status=discovered"
```

### Clear Discovered Servers

Clear the list of discovered servers.

**Endpoint:** `DELETE /proxy/discovery/servers`

**Response:**

```json
{
  "data": {
    "cleared_count": 5
  },
  "message": "Discovered servers cleared",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/proxy/discovery/servers \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

## Tool Management

### List Tools

Get all tools from wrapped servers.

**Endpoint:** `GET /proxy/tools`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `server_id` | string | No | Filter by server ID |
| `category` | string | No | Filter by category |
| `search` | string | No | Search in tool names and descriptions |

**Response:**

```json
{
  "data": [
    {
      "name": "read_file",
      "description": "Read file contents",
      "server_id": "file-server_0",
      "server_name": "file-server",
      "categories": ["file-operations"],
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "File path"
          }
        },
        "required": ["path"]
      }
    }
  ],
  "message": "Tools retrieved successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:8000/proxy/tools?server_id=file-server_0"
```

### Call Tool

Execute a tool on a wrapped server.

**Endpoint:** `POST /proxy/tools/{tool_name}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | Yes | Tool name |

**Request Body:**

```json
{
  "arguments": {},
  "server_id": "string"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `arguments` | object | Yes | Tool arguments |
| `server_id` | string | No | Specific server ID (auto-selected if not provided) |

**Response:**

```json
{
  "data": {
    "result": "File contents...",
    "server_id": "file-server_0",
    "execution_time": 0.125,
    "status": "success"
  },
  "message": "Tool executed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/proxy/tools/read_file \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "arguments": {
      "path": "/path/to/file.txt"
    },
    "server_id": "file-server_0"
  }'
```

## Statistics and Metrics

### Get Statistics

Get proxy wrapper statistics and metrics.

**Endpoint:** `GET /proxy/stats`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period (1h, 24h, 7d, 30d) |

**Response:**

```json
{
  "data": {
    "servers": {
      "total": 5,
      "healthy": 4,
      "unhealthy": 1
    },
    "tools": {
      "total": 25,
      "by_category": {
        "file-operations": 10,
        "data-processing": 8,
        "network": 7
      }
    },
    "requests": {
      "total": 1250,
      "successful": 1200,
      "failed": 50,
      "avg_response_time": 0.125
    },
    "discovery": {
      "last_run": "2024-01-15T10:30:00Z",
      "discovered_count": 3,
      "auto_registered": 2
    }
  },
  "message": "Statistics retrieved",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:8000/proxy/stats?period=24h"
```

## Error Codes

| Code | Description |
|------|-------------|
| `PROXY_SERVER_NOT_FOUND` | Server not found |
| `PROXY_SERVER_ALREADY_EXISTS` | Server already registered |
| `PROXY_CONNECTION_FAILED` | Failed to connect to server |
| `PROXY_AUTHENTICATION_FAILED` | Authentication failed |
| `PROXY_TOOL_NOT_FOUND` | Tool not found |
| `PROXY_TOOL_EXECUTION_FAILED` | Tool execution failed |
| `PROXY_DISCOVERY_FAILED` | Server discovery failed |
| `PROXY_HEALTH_CHECK_FAILED` | Health check failed |
| `PROXY_INVALID_CONFIG` | Invalid configuration |
| `PROXY_TIMEOUT` | Request timeout |
| `PROXY_RATE_LIMITED` | Rate limit exceeded |

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authentication endpoints**: 10 requests per minute
- **Server management**: 60 requests per minute
- **Tool execution**: 100 requests per minute
- **Health checks**: 30 requests per minute
- **Discovery**: 5 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642234567
```

## Pagination

List endpoints support pagination:

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `per_page` | integer | No | 20 | Items per page |

**Response Headers:**

```
X-Total-Count: 100
X-Page-Count: 5
X-Current-Page: 1
X-Per-Page: 20
```

## WebSocket Support

Some endpoints support WebSocket connections for real-time updates:

**WebSocket URL:** `ws://localhost:8000/proxy/ws`

**Events:**

- `server.registered` - Server registered
- `server.unregistered` - Server unregistered
- `server.health_changed` - Server health status changed
- `tool.called` - Tool executed
- `discovery.completed` - Discovery completed

**Example:**

```javascript
const ws = new WebSocket('ws://localhost:8000/proxy/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

This comprehensive API reference covers all proxy wrapper endpoints and their usage. 