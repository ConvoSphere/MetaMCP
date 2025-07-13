# Environment Variables

This document describes all environment variables used by the MetaMCP application.

## Overview

MetaMCP uses Pydantic Settings for configuration management, which automatically loads environment variables. All configuration can be set via environment variables, with sensible defaults provided.

## Quick Start

1. Copy `env.example` to `.env`:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your specific values
3. For Docker, environment variables are defined in `docker-compose.yml`

## Environment Variables Reference

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `MetaMCP` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
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

### Vector Database Settings (Weaviate)

| Variable | Default | Description |
|----------|---------|-------------|
| `WEAVIATE_URL` | `http://localhost:8080` | Weaviate server URL |
| `WEAVIATE_API_KEY` | `None` | Weaviate API key (optional) |
| `VECTOR_DIMENSION` | `1536` | Vector embedding dimension |

### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider (openai/fallback) |
| `OPENAI_API_KEY` | `None` | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4` | OpenAI model name |
| `OPENAI_BASE_URL` | `None` | OpenAI base URL (for custom endpoints) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-ada-002` | OpenAI embedding model |

### Authentication Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT secret key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token expiry time |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPA_URL` | `http://localhost:8181` | Open Policy Agent URL |
| `OPA_TIMEOUT` | `5` | OPA request timeout in seconds |

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
| `TOOL_REGISTRY_CACHE_TTL` | `300` | Tool registry cache TTL in seconds |

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

### Redis Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `REDIS_PASSWORD` | `None` | Redis password |
| `REDIS_DB` | `0` | Redis database number |

## Environment-Specific Configuration

### Development Environment

```bash
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
RELOAD=true
TELEMETRY_ENABLED=false
VECTOR_SEARCH_ENABLED=false
```

### Staging Environment

```bash
DEBUG=false
ENVIRONMENT=staging
LOG_LEVEL=INFO
RELOAD=false
TELEMETRY_ENABLED=true
```

### Production Environment

```bash
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=WARNING
RELOAD=false
TELEMETRY_ENABLED=true
DOCS_ENABLED=false
```

## Docker Configuration

For Docker deployments, environment variables are defined in `docker-compose.yml`:

```yaml
environment:
  - APP_NAME=MetaMCP
  - DEBUG=true
  - ENVIRONMENT=development
  # ... other variables
```

## Security Considerations

1. **Never commit `.env` files** - They may contain sensitive information
2. **Use strong SECRET_KEY** - Generate a secure random key for production
3. **Secure API keys** - Store API keys securely and rotate regularly
4. **Environment separation** - Use different values for dev/staging/production

## Validation

Environment variables are automatically validated by Pydantic:

- Enum values are checked against allowed options
- Numeric values are validated for range and type
- Required fields are enforced
- Default values are applied when not specified

## Troubleshooting

### Common Issues

1. **Missing required variables**: Check that all required variables are set
2. **Invalid values**: Ensure values match expected types and ranges
3. **Environment file not loaded**: Verify `.env` file exists and is readable
4. **Docker environment**: Check `docker-compose.yml` environment section

### Debug Configuration

Enable debug mode to see configuration loading:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

This will show detailed information about which environment variables are loaded and their values. 