# Quick Start Guide

Get MetaMCP up and running in minutes with this quick start guide.

## Prerequisites

- Docker and Docker Compose
- 4GB RAM (for Weaviate)
- Python 3.8+ (for development)

## Option 1: Docker Compose (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/lichtbaer/MetaMCP.git
cd MetaMCP
```

### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- MetaMCP Server (port 8000)
- PostgreSQL Database (port 5432)
- Weaviate Vector Database (port 8088)
- Redis Cache (port 6379)
- OPA Policy Engine (port 8181)
- Admin UI (port 8080)
- Prometheus (port 9090)
- Grafana (port 3000)

### 3. Verify Installation

```bash
# Check service health
curl http://localhost:8000/api/v1/health

# Access admin UI
open http://localhost:8080
```

## Option 2: Development Setup

### 1. Install Dependencies

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Start Infrastructure

```bash
# Start required services
docker-compose up -d postgres weaviate redis opa
```

### 4. Run MetaMCP

```bash
# Start the server
python -m metamcp.main
```

## First Steps

### 1. Access the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# List available tools
curl http://localhost:8000/api/v1/tools
```

### 2. Use the Admin UI

Open http://localhost:8080 in your browser:
- **Username**: admin
- **Password**: admin123

### 3. Connect an MCP Client

```python
import asyncio
from metamcp.client import MetaMCPClient

async def main():
    client = MetaMCPClient("http://localhost:8000")
    
    # Search for tools
    tools = await client.search_tools("database query")
    print(f"Found {len(tools)} tools")
    
    # Execute a tool
    result = await client.execute_tool("database_query", {
        "query": "SELECT * FROM users LIMIT 10"
    })
    print(result)

asyncio.run(main())
```

## Configuration

### Environment Variables

Key configuration options:

```bash
# Database
DATABASE_URL=postgresql://metamcp:metamcp@localhost:5432/metamcp

# Vector Database
WEAVIATE_URL=http://localhost:8088

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

### Default Credentials

- **Admin UI**: admin / admin123
- **Database**: metamcp / metamcp
- **Redis**: No password (development)

## Next Steps

1. **[Installation Guide](installation.md)** - Detailed installation instructions
2. **[Configuration Guide](configuration.md)** - Advanced configuration options
3. **[User Guide](../user-guide/overview.md)** - Learn how to use MetaMCP
4. **[Developer Guide](../developer-guide/development-setup.md)** - Set up development environment

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker-compose logs metamcp-server

# Check resource usage
docker stats
```

**Database connection failed:**
```bash
# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

**Weaviate not accessible:**
```bash
# Check Weaviate health
curl http://localhost:8088/v1/.well-known/ready

# Restart Weaviate
docker-compose restart weaviate
```

### Getting Help

- **Documentation**: Check the [Troubleshooting Guide](../reference/troubleshooting.md)
- **GitHub Issues**: [Report problems](https://github.com/lichtbaer/MetaMCP/issues)
- **Discord**: [Community support](https://discord.gg/metamcp) 