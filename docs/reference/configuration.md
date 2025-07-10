# Configuration Reference

MetaMCP uses a comprehensive configuration system based on Pydantic Settings with environment variable support.

## Configuration Sources

Configuration is loaded in the following order (later sources override earlier ones):

1. **Default values** (hardcoded in Settings class)
2. **Environment variables**
3. **`.env` file** (if present)
4. **Command line arguments** (if provided)

## Environment Variables

All configuration options can be set via environment variables. Variable names are automatically converted from camelCase to UPPER_SNAKE_CASE.

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `MetaMCP` | Application name |
| `APP_VERSION` | `0.1.0` | Application version |
| `DEBUG` | `false` | Enable debug mode |
| `ENVIRONMENT` | `development` | Environment (development/staging/production) |

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8000` | Server port |
| `WORKERS` | `1` | Number of worker processes |

### Database Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:password@localhost/metamcp` | Database connection URL |
| `DATABASE_POOL_SIZE` | `10` | Database connection pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | Database max overflow connections |

### Vector Database Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `WEAVIATE_URL` | `http://localhost:8080` | Weaviate server URL |
| `WEAVIATE_API_KEY` | `None` | Weaviate API key |
| `VECTOR_DIMENSION` | `1536` | Vector embedding dimension |

### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider (openai/fallback) |
| `OPENAI_API_KEY` | `None` | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4` | OpenAI model for text generation |
| `OPENAI_BASE_URL` | `None` | OpenAI base URL (for Azure) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-ada-002` | OpenAI embedding model |

### Authentication Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key-change-in-production` | Secret key for JWT tokens |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token expiration time |

### OAuth Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_OAUTH_CLIENT_ID` | `None` | Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `None` | Google OAuth client secret |
| `GITHUB_OAUTH_CLIENT_ID` | `None` | GitHub OAuth client ID |
| `GITHUB_OAUTH_CLIENT_SECRET` | `None` | GitHub OAuth client secret |
| `MICROSOFT_OAUTH_CLIENT_ID` | `None` | Microsoft OAuth client ID |
| `MICROSOFT_OAUTH_CLIENT_SECRET` | `None` | Microsoft OAuth client secret |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPA_URL` | `http://localhost:8181` | Open Policy Agent URL |
| `OPA_TIMEOUT` | `5` | OPA request timeout |

### Logging Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `LOG_FORMAT` | `json` | Log format (json/text) |

### Monitoring Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9090` | Prometheus metrics port |

### OpenTelemetry Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OTLP_ENDPOINT` | `None` | OTLP endpoint for telemetry |
| `OTLP_INSECURE` | `true` | Use insecure connection for OTLP |
| `TELEMETRY_ENABLED` | `true` | Enable OpenTelemetry telemetry |

### CORS Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow CORS credentials |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_REQUESTS` | `100` | Rate limit requests per minute |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |

### Tool Registry Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOL_REGISTRY_ENABLED` | `true` | Enable tool registry |
| `TOOL_REGISTRY_AUTO_DISCOVERY` | `true` | Auto-discover tools |
| `TOOL_REGISTRY_CACHE_TTL` | `300` | Tool registry cache TTL |

### Vector Search Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_SEARCH_ENABLED` | `true` | Enable vector search |
| `VECTOR_SEARCH_SIMILARITY_THRESHOLD` | `0.7` | Vector search similarity threshold |
| `VECTOR_SEARCH_MAX_RESULTS` | `10` | Max vector search results |

### Policy Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `POLICY_ENFORCEMENT_ENABLED` | `true` | Enable policy enforcement |
| `POLICY_DEFAULT_ALLOW` | `false` | Default policy allow |

### Admin Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_ENABLED` | `true` | Enable admin interface |
| `ADMIN_PORT` | `8501` | Admin interface port |

### Development Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `RELOAD` | `false` | Auto-reload on changes |
| `DOCS_ENABLED` | `true` | Enable API documentation |

## Configuration Examples

### Development Environment

```env
# Development settings
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
TELEMETRY_ENABLED=false

# OpenAI (required for embeddings)
OPENAI_API_KEY=sk-your-openai-api-key

# Security (change in production)
SECRET_KEY=dev-secret-key-change-in-production

# Vector database (optional)
WEAVIATE_URL=http://localhost:8080

# OPA (optional)
OPA_URL=http://localhost:8181
```

### Production Environment

```env
# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
TELEMETRY_ENABLED=true

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Security (use strong secret)
SECRET_KEY=your-very-secure-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@db.example.com/metamcp

# Vector database
WEAVIATE_URL=https://weaviate.example.com
WEAVIATE_API_KEY=your-weaviate-api-key

# OAuth (configure as needed)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# Monitoring
OTLP_ENDPOINT=https://otel.example.com:4317
OTLP_INSECURE=false

# Rate limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

### Docker Environment

```env
# Docker settings
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database (Docker Compose)
DATABASE_URL=postgresql://metamcp:metamcp@postgres:5432/metamcp

# Vector database (Docker Compose)
WEAVIATE_URL=http://weaviate:8080

# OPA (Docker Compose)
OPA_URL=http://opa:8181

# Monitoring (Docker Compose)
PROMETHEUS_METRICS_PORT=9090
```

## Configuration Validation

MetaMCP validates configuration on startup:

### Required Settings

- **Production**: `SECRET_KEY` must be set and not default
- **Production**: `OPENAI_API_KEY` must be configured
- **Vector Search**: `WEAVIATE_URL` required if vector search enabled

### Environment-Specific Validation

```python
# Development
if environment == "development":
    # Relaxed validation
    pass

# Production
if environment == "production":
    if not secret_key or secret_key == "your-secret-key-change-in-production":
        raise ValueError("SECRET_KEY must be set in production")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY must be configured")
```

## Configuration Management

### Loading Configuration

```python
from metamcp.config import get_settings

# Get settings instance
settings = get_settings()

# Access configuration
print(f"Server running on {settings.host}:{settings.port}")
print(f"Environment: {settings.environment}")
```

### Reloading Configuration

```python
from metamcp.config import reload_settings

# Reload settings (useful for testing)
settings = reload_settings()
```

### Environment-Specific Settings

```python
from metamcp.config import get_environment_settings

# Get environment-specific overrides
env_settings = get_environment_settings()

# Apply to current settings
settings = get_settings()
for key, value in env_settings.items():
    setattr(settings, key, value)
```

## Configuration Best Practices

### Security

1. **Never commit secrets**: Use environment variables or secure secret management
2. **Use strong secrets**: Generate cryptographically secure random keys
3. **Rotate secrets**: Regularly rotate API keys and secrets
4. **Limit permissions**: Use least-privilege access for external services

### Performance

1. **Database pooling**: Configure appropriate pool sizes for your workload
2. **Rate limiting**: Set appropriate limits for your use case
3. **Caching**: Enable caching where appropriate
4. **Monitoring**: Enable telemetry in production

### Scalability

1. **Horizontal scaling**: Use multiple workers for high load
2. **Database scaling**: Use read replicas for high-traffic scenarios
3. **Caching**: Implement Redis for session and cache storage
4. **Load balancing**: Use reverse proxies for multiple instances

### Development

1. **Environment separation**: Use different configs for dev/staging/prod
2. **Debug mode**: Enable debug features only in development
3. **Hot reloading**: Enable auto-reload for faster development
4. **Local services**: Use Docker Compose for local development

## Troubleshooting Configuration

### Common Issues

1. **Missing API key**:
   ```
   Error: OpenAI API key not configured
   Solution: Set OPENAI_API_KEY environment variable
   ```

2. **Invalid database URL**:
   ```
   Error: Database connection failed
   Solution: Check DATABASE_URL format and connectivity
   ```

3. **Weaviate not accessible**:
   ```
   Error: Weaviate server not accessible
   Solution: Verify WEAVIATE_URL and network connectivity
   ```

4. **Invalid secret key**:
   ```
   Error: SECRET_KEY must be set in production
   Solution: Set a strong secret key for production
   ```

### Configuration Validation

```bash
# Validate configuration
python -c "from metamcp.config import validate_configuration; validate_configuration()"

# Check environment variables
python -c "from metamcp.config import get_settings; print(get_settings().dict())"
```

### Environment Variable Debugging

```bash
# List all environment variables
env | grep -i metamcp

# Check specific variables
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:-not set}"
echo "DATABASE_URL: ${DATABASE_URL:-not set}"
echo "SECRET_KEY: ${SECRET_KEY:-not set}"
``` 