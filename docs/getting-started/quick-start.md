# Quick Start Guide

Get MetaMCP up and running in minutes with this quick start guide.

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key (for embeddings and text generation)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/lichtbaer/MetaMCP.git
cd MetaMCP
```

### 2. Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env
```

Edit the `.env` file with your settings:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Vector Database (Optional)
WEAVIATE_URL=http://localhost:8080

# OPA Policy Engine (Optional)
OPA_URL=http://localhost:8181
```

### 4. Start the Server

```bash
# Start the development server
python -m metamcp.main
```

The server will be available at `http://localhost:8000`

## Verify Installation

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-07-10T19:30:00Z"
}
```

### 2. API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Admin Interface

Access the admin interface at:
- **Admin UI**: http://localhost:8000/admin

## First Steps

### 1. Register a Tool

```bash
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "calculator",
    "description": "Perform mathematical calculations",
    "endpoint": "http://localhost:8001",
    "categories": ["math", "calculation"],
    "input_schema": {
      "type": "object",
      "properties": {
        "expression": {"type": "string"}
      },
      "required": ["expression"]
    }
  }'
```

### 2. Search for Tools

```bash
curl -X POST http://localhost:8000/api/tools/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mathematical calculations",
    "max_results": 5
  }'
```

### 3. Connect an MCP Client

Use any MCP-compatible client to connect to the server:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async with stdio_client(StdioServerParameters(
    command="python", 
    args=["-m", "metamcp.mcp.server"]
)) as (read, write):
    async with ClientSession(read, write) as session:
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {tools}")
```

## Development Mode

For development, you can enable additional features:

```env
# Development settings
DEBUG=true
RELOAD=true
DOCS_ENABLED=true
LOG_LEVEL=DEBUG
TELEMETRY_ENABLED=false
```

## Next Steps

- **[Configuration Guide](configuration.md)** - Detailed configuration options
- **[API Reference](../user-guide/api-reference.md)** - Complete API documentation
- **[Tool Management](../user-guide/tool-management.md)** - Managing tools and capabilities
- **[Security Setup](../user-guide/security.md)** - Security configuration

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in .env file
   PORT=8001
   ```

2. **OpenAI API key not configured**
   ```bash
   # Add your OpenAI API key to .env
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Dependencies not found**
   ```bash
   # Reinstall dependencies
   uv pip install -r requirements.txt
   ```

### Getting Help

- Check the [Troubleshooting Guide](../reference/troubleshooting.md)
- Report issues on [GitHub](https://github.com/lichtbaer/MetaMCP/issues)
- Join our [Discord community](https://discord.gg/metamcp) 