# Configuration

MetaMCP-Konfiguration über Umgebungsvariablen.

## 🔧 Basis-Konfiguration

```bash
# .env
APP_NAME=MetaMCP
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=1
```

## 🗄️ Datenbank

```bash
# SQLite (Development)
DATABASE_URL=sqlite:///./metamcp.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://user:pass@localhost/metamcp
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## 🔐 Authentication

```bash
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🛠️ Tools & MCP

```bash
# Tool Registry
TOOL_REGISTRY_ENABLED=true
TOOL_REGISTRY_AUTO_DISCOVERY=true
TOOL_REGISTRY_CACHE_TTL=300

# Vector Search
VECTOR_SEARCH_ENABLED=false
VECTOR_SEARCH_SIMILARITY_THRESHOLD=0.7
VECTOR_SEARCH_MAX_RESULTS=10
```

## 🔒 Security

```bash
# OPA Policy Engine
OPA_URL=http://localhost:8181
OPA_TIMEOUT=5

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# CORS
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true
```

## 📊 Monitoring

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Prometheus
PROMETHEUS_METRICS_PORT=9090

# OpenTelemetry
OTLP_ENDPOINT=
OTLP_INSECURE=true
TELEMETRY_ENABLED=false
```

## 🎛️ Admin Interface

```bash
ADMIN_ENABLED=true
ADMIN_PORT=9501
ADMIN_API_URL=http://localhost:8000/api/v1/admin/
ADMIN_AUTO_REFRESH_INTERVAL=30000
```

## 🗃️ Cache & Redis

```bash
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
```

## 🧪 Development

```bash
# Hot Reload
RELOAD=true

# Documentation
DOCS_ENABLED=true

# Testing
TESTING=true
```

## 🚀 Production

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=very-long-secret-key-here
CORS_ORIGINS=["https://yourdomain.com"]

# Performance
WORKERS=4
DATABASE_POOL_SIZE=20

# Monitoring
LOG_LEVEL=WARNING
TELEMETRY_ENABLED=true
```

## 📋 Vollständige .env

```bash
# Application
APP_NAME=MetaMCP
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:pass@localhost/metamcp
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Authentication
SECRET_KEY=your-production-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Security
OPA_URL=http://opa:8181
OPA_TIMEOUT=5
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Tools
TOOL_REGISTRY_ENABLED=true
TOOL_REGISTRY_AUTO_DISCOVERY=true
TOOL_REGISTRY_CACHE_TTL=300
VECTOR_SEARCH_ENABLED=false
VECTOR_SEARCH_SIMILARITY_THRESHOLD=0.7
VECTOR_SEARCH_MAX_RESULTS=10

# Monitoring
LOG_LEVEL=WARNING
LOG_FORMAT=json
PROMETHEUS_METRICS_PORT=9090
OTLP_ENDPOINT=http://otel:4317
OTLP_INSECURE=false
TELEMETRY_ENABLED=true

# Admin
ADMIN_ENABLED=true
ADMIN_PORT=9501
ADMIN_API_URL=http://localhost:8000/api/v1/admin/
ADMIN_AUTO_REFRESH_INTERVAL=30000

# Cache
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
```

## 🔍 Konfiguration prüfen

```bash
# Alle Einstellungen anzeigen
curl http://localhost:8000/api/v1/admin/config

# Health Check
curl http://localhost:8000/api/v1/health
```