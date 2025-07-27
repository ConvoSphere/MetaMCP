# API Reference

RESTful API für MetaMCP.

## 🔐 Authentication

Alle Endpunkte benötigen JWT-Token:

```bash
# Login
curl -X POST "http://localhost:9000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Token verwenden
curl -X GET "http://localhost:9000/api/v1/tools" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📋 Endpunkte

### Tools

```bash
# Tool registrieren
POST /api/v1/tools
{
  "name": "database_query",
  "description": "SQL queries ausführen",
  "endpoint_url": "http://localhost:8001",
  "schema": {"input": {}, "output": {}}
}

# Tools auflisten
GET /api/v1/tools?page=1&limit=10

# Tool ausführen
POST /api/v1/tools/{tool_id}/execute
{
  "arguments": {"query": "SELECT * FROM users"}
}
```

### Users

```bash
# User erstellen
POST /api/v1/users
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "roles": ["user"]
}

# Users auflisten
GET /api/v1/users?page=1&limit=10

# User aktualisieren
PUT /api/v1/users/{user_id}
{
  "email": "new@example.com"
}
```

### Workflows

```bash
# Workflow erstellen
POST /api/v1/workflows
{
  "name": "data_processing",
  "steps": [
    {
      "tool_name": "fetch_data",
      "arguments": {"source": "database"}
    },
    {
      "tool_name": "process_data",
      "arguments": {"operation": "transform"}
    }
  ]
}

# Workflow ausführen
POST /api/v1/workflows/{workflow_id}/execute
{
  "parameters": {"database": "production"}
}
```

### Admin API

```bash
# Dashboard-Daten
GET /api/v1/admin/dashboard

# System-Metriken
GET /api/v1/admin/system/metrics

# User-Management
GET /api/v1/admin/users
POST /api/v1/admin/users
PUT /api/v1/admin/users/{user_id}
DELETE /api/v1/admin/users/{user_id}

# Tool-Management
GET /api/v1/admin/tools
POST /api/v1/admin/tools
PUT /api/v1/admin/tools/{tool_id}
DELETE /api/v1/admin/tools/{tool_id}

# System-Logs
GET /api/v1/admin/logs?level=ERROR&limit=100

# System-Restart
POST /api/v1/admin/system/restart
```

## 📊 Response Format

### Success
```json
{
  "status": "success",
  "data": {...},
  "message": "Operation completed"
}
```

### Error
```json
{
  "status": "error",
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10
  }
}
```

## 🔍 Filtering & Search

```bash
# Tools nach Kategorie
GET /api/v1/tools?category=database

# Users nach Rolle
GET /api/v1/users?role=admin

# Suche in Namen/Beschreibung
GET /api/v1/tools?search=query

# Status-Filter
GET /api/v1/tools?status=active
```

## 📈 Monitoring

### Health Checks
```bash
# Basic Health
GET /api/v1/health

# Detailed Health
GET /api/v1/health/detailed

# Readiness Probe
GET /api/v1/health/ready
```

### Metrics
```bash
# Prometheus Metrics
GET /metrics
```

## 🔒 Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## 📚 OpenAPI Docs

Interaktive Dokumentation: http://localhost:9000/docs