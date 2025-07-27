# Proxy Wrapper Quick Start

Get started with the MetaMCP Proxy Wrapper in minutes. This guide will help you wrap your first MCP server and start using enhanced features.

## Prerequisites

- MetaMCP server running (see [Quick Start](quick-start.md))
- At least one MCP server to wrap
- Basic understanding of MCP protocol

## Step 1: Start MetaMCP

First, ensure MetaMCP is running:

```bash
# Start MetaMCP
python -m metamcp.main

# Or using Docker
docker-compose up -d
```

MetaMCP will be available at `http://localhost:8000`.

## Step 2: Register Your First Server

Register an MCP server for wrapping:

```bash
curl -X POST http://localhost:8000/proxy/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-file-server",
    "endpoint": "http://localhost:8001",
    "transport": "http",
    "categories": ["file-operations"],
    "description": "My custom file operations server"
  }'
```

Response:
```json
{
  "data": {
    "server_id": "my-file-server_0"
  },
  "message": "Server registered successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Step 3: Check Server Health

Verify your server is healthy:

```bash
curl http://localhost:8000/proxy/health
```

Response:
```json
{
  "data": {
    "my-file-server_0": {
      "server_id": "my-file-server_0",
      "status": "healthy",
      "last_seen": "2024-01-15T10:30:00Z",
      "healthy": true,
      "error": null
    }
  }
}
```

## Step 4: List Available Tools

See what tools are available from your wrapped server:

```bash
curl http://localhost:8000/proxy/tools
```

Response:
```json
{
  "data": [
    {
      "name": "read_file",
      "description": "Read file contents",
      "server_id": "my-file-server_0",
      "server_name": "my-file-server",
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
  ]
}
```

## Step 5: Execute a Tool

Call a tool on your wrapped server:

```bash
curl -X POST http://localhost:8000/proxy/tools/read_file \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "path": "/path/to/file.txt"
    }
  }'
```

Response:
```json
{
  "data": {
    "result": "File contents...",
    "server_id": "my-file-server_0",
    "execution_time": 0.125,
    "status": "success"
  }
}
```

## Step 6: Discover Servers Automatically

Let MetaMCP discover MCP servers on your network:

```bash
curl -X POST http://localhost:8000/proxy/discovery \
  -H "Content-Type: application/json" \
  -d '{
    "network_discovery": true,
    "ports": [8001, 8002, 8003],
    "base_urls": ["http://localhost", "http://127.0.0.1"],
    "timeout": 5
  }'
```

Response:
```json
{
  "data": {
    "discovered_count": 2,
    "servers": [
      {
        "name": "file-server",
        "endpoint": "http://localhost:8001",
        "transport": "http",
        "status": "discovered",
        "tools": [
          {
            "name": "read_file",
            "description": "Read file contents"
          }
        ]
      }
    ],
    "auto_registered": 1,
    "failed_discoveries": 0
  }
}
```

## Python Client Example

Use the Python client for programmatic access:

```python
import asyncio
from metamcp.proxy import ProxyManager, WrappedServerConfig

async def main():
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    await proxy_manager.initialize()
    
    # Register a server
    config = WrappedServerConfig(
        name="python-file-server",
        endpoint="http://localhost:8001",
        transport="http",
        categories=["file-operations"]
    )
    
    server_id = await proxy_manager.register_server(config)
    print(f"Registered server: {server_id}")
    
    # List servers
    servers = await proxy_manager.list_servers()
    for server in servers:
        print(f"Server: {server.name} - {server.status}")
    
    # Check health
    health = await proxy_manager.check_health(server_id)
    print(f"Health: {health.healthy}")
    
    # Call a tool
    result = await proxy_manager.call_tool("read_file", {"path": "/test.txt"})
    print(f"Result: {result}")

# Run the example
asyncio.run(main())
```

## Docker Compose Example

Use Docker Compose for easy deployment:

```yaml
version: '3.8'
services:
  metamcp:
    image: metamcp:latest
    ports:
      - "8000:8000"
    environment:
      - PROXY_ENABLED=true
      - DISCOVERY_ENABLED=true
      - PROXY_HEALTH_CHECK_INTERVAL=30
    volumes:
      - ./config:/app/config
    depends_on:
      - weaviate
      - opa
  
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=none
      - ENABLE_MODULES=text2vec-openai
      - CLUSTER_HOSTNAME=node1
  
  opa:
    image: openpolicyagent/opa:latest
    ports:
      - "8181:8181"
    command: run --server --addr :8181
    volumes:
      - ./policies:/policies
```

## Configuration Examples

### Basic Configuration

```yaml
# config/proxy.yaml
proxy:
  enabled: true
  discovery:
    enabled: true
    network_discovery: true
    ports: [8001, 8002, 8003]
    base_urls: ["http://localhost"]
  
  health_check:
    interval: 30
    timeout: 5
    max_failures: 3
  
  servers:
    - name: "file-server"
      endpoint: "http://localhost:8001"
      transport: "http"
      categories: ["file-operations"]
    
    - name: "data-server"
      endpoint: "http://localhost:8002"
      transport: "http"
      categories: ["data-processing"]
```

### Advanced Configuration

```yaml
# config/proxy-advanced.yaml
proxy:
  enabled: true
  
  # Discovery settings
  discovery:
    enabled: true
    network_discovery: true
    service_discovery: true
    file_discovery: true
    ports: [8001, 8002, 8003, 8004, 8005]
    base_urls: ["http://localhost", "http://127.0.0.1"]
    config_paths: ["./mcp-servers.json"]
    timeout: 5
    max_concurrent: 10
  
  # Health check settings
  health_check:
    interval: 30
    timeout: 5
    max_failures: 3
  
  # Security settings
  security:
    auth_required: false
    security_level: "medium"
  
  # Performance settings
  performance:
    max_concurrent_requests: 10
    cache_enabled: true
    cache_ttl: 300
    load_balancing_enabled: true
    load_balancing_strategy: "round_robin"
  
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 100
  
  # Servers
  servers:
    - name: "file-server"
      endpoint: "http://localhost:8001"
      transport: "http"
      auth_required: false
      timeout: 30
      retry_attempts: 3
      security_level: "medium"
      categories: ["file-operations"]
      description: "File operations server"
    
    - name: "data-server"
      endpoint: "http://localhost:8002"
      transport: "http"
      auth_required: true
      auth_token: "your-auth-token"
      timeout: 60
      retry_attempts: 5
      security_level: "high"
      categories: ["data-processing", "analytics"]
      description: "Data processing server"
```

## Environment Variables

Configure the proxy wrapper using environment variables:

```bash
# Enable proxy wrapper
export PROXY_ENABLED=true

# Enable discovery
export PROXY_DISCOVERY_ENABLED=true

# Health check settings
export PROXY_HEALTH_CHECK_INTERVAL=30
export PROXY_HEALTH_CHECK_TIMEOUT=5

# Performance settings
export PROXY_MAX_RETRY_ATTEMPTS=3
export PROXY_DEFAULT_TIMEOUT=30
export PROXY_MAX_CONCURRENT_REQUESTS=10

# Rate limiting
export PROXY_RATE_LIMIT_ENABLED=true
export PROXY_RATE_LIMIT_REQUESTS=100

# Caching
export PROXY_CACHE_ENABLED=true
export PROXY_CACHE_TTL=300

# Load balancing
export PROXY_LOAD_BALANCING_ENABLED=true
export PROXY_LOAD_BALANCING_STRATEGY=round_robin
```

## Next Steps

1. **Explore the API**: Check out the [Proxy API Reference](../reference/proxy-api.md)
2. **Read the User Guide**: Learn more in the [Proxy Wrapper Guide](../user-guide/proxy-wrapper.md)
3. **Develop Custom Features**: See the [Proxy Development Guide](../developer-guide/proxy-development.md)
4. **Configure Security**: Set up authentication and authorization
5. **Monitor Performance**: Use the built-in monitoring and metrics

## Troubleshooting

### Common Issues

1. **Server Connection Failed**
   ```bash
   # Check if server is running
   curl http://localhost:8001/health
   
   # Check network connectivity
   ping localhost
   ```

2. **Authentication Errors**
   ```bash
   # Verify auth token
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/proxy/servers
   ```

3. **Health Check Failures**
   ```bash
   # Check specific server health
   curl http://localhost:8000/proxy/health?server_id=my-server_0
   
   # View logs
   docker logs metamcp-proxy
   ```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m metamcp.main
```

### Health Check Debugging

```bash
# Check all servers
curl http://localhost:8000/proxy/health

# Check specific server
curl "http://localhost:8000/proxy/health?server_id=my-server_0"

# Force health check
curl -X POST http://localhost:8000/proxy/health \
  -H "Content-Type: application/json" \
  -d '{"server_id": "my-server_0"}'
```

This quick start guide will get you up and running with the MetaMCP Proxy Wrapper in no time! 