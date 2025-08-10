# MetaMCP

**Meta Model Context Protocol** - Ein modulares System für Tool-Komposition und MCP-Management mit umfassendem API Versioning und erweiterten Transport-Funktionalitäten.

## 🚀 Schnellstart

### Installation
```bash
git clone https://github.com/lichtbaer/MetaMCP.git
cd metamcp
pip install -r requirements.txt
```

### Konfiguration
```bash
# Environment-Konfiguration kopieren und anpassen
cp env.example .env

# Sichere Secret Keys generieren
python scripts/validate_env.py --setup

# Konfiguration validieren
python scripts/validate_env.py
```

### Start
```bash
# Backend (WebSocket/HTTP)
python -m metamcp.main

# Stdio Transport (für Container/CLI)
python -m metamcp.mcp.server --stdio

# Admin Interface (optional)
python scripts/start_admin.py
```

### Docker
```bash
docker-compose up -d
```

**Zugriff:**
- API: http://localhost:9000
- Admin: http://localhost:9501
- Docs: http://localhost:9000/docs
- API Versions: http://localhost:9000/api/versions
- MCP WebSocket: ws://localhost:9000/mcp/ws

## 🔄 MCP Transport-Funktionalitäten

### Verfügbare Transport-Layer

- **WebSocket**: Vollständige MCP-Protokoll-Unterstützung über WebSocket
- **HTTP**: REST-basierte MCP-Kommunikation
- **stdio**: Standard-Ein-/Ausgabe für Container und CLI-Tools

### Transport-Verwendung

**WebSocket Transport:**
```bash
# WebSocket Server starten
python -m metamcp.mcp.server --websocket --port 8080

# Client-Verbindung
wscat -c ws://localhost:8080/mcp/ws
```

**Stdio Transport:**
```bash
# Stdio Server starten
python -m metamcp.mcp.server --stdio

# Mit Test Client
python -m metamcp.mcp.server --stdio | python scripts/test_stdio_mcp.py
```

**HTTP Transport:**
```bash
# HTTP Endpoints verfügbar unter
curl http://localhost:9000/mcp/tools
curl http://localhost:9000/mcp/tools/test_tool/execute
```

### Streaming-Support

Das System unterstützt Streaming-Antworten für lange laufende Operationen:

```python
# Streaming Tool Execution
async for chunk in mcp_server._handle_call_tool_streaming("tool_name", args):
    print(f"Chunk: {chunk}")

# Progress Updates
await mcp_server.send_progress_update("op_id", 75.0, "Processing...")

# Event Broadcasting
await mcp_server.broadcast_event("tool_executed", {"tool": "name"})
```

## 🔄 API Versioning

Das MetaMCP System unterstützt umfassendes API Versioning mit folgenden Features:

### Verfügbare Versionen

- **v1**: Initiale API-Version mit Kernfunktionalität
- **v2**: Erweiterte API-Version mit verbesserten Features

### Version Management

```bash
# Alle verfügbaren Versionen anzeigen
curl http://localhost:9000/api/versions

# Spezifische Version verwenden
curl http://localhost:9000/api/v2/tools

# Zur neuesten Version weiterleiten
curl http://localhost:9000/api/latest
```

### Version-spezifische Endpunkte

**v1 Endpunkte:**
- `/api/v1/auth/*` - Authentifizierung
- `/api/v1/tools/*` - Tool-Management
- `/api/v1/health/*` - Health Checks
- `/api/v1/admin/*` - Admin Interface

**v2 Endpunkte (erweitert):**
- `/api/v2/auth/*` - Erweiterte Authentifizierung mit Session-Management
- `/api/v2/tools/*` - Erweitertes Tool-Management mit verbesserter Suche
- `/api/v2/health/*` - Umfassende Health Checks mit Metriken
- `/api/v2/analytics/*` - Erweiterte Analytics und Reporting

### Migration von v1 zu v2

```bash
# v1 (Legacy)
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# v2 (Enhanced)
curl -X POST http://localhost:9000/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass", "remember_me": true}'
```

## 🔒 Sicherheit

### Kritische Sicherheitsmaßnahmen

1. **Secret Key Management**
   ```bash
   # Sicheren Secret Key generieren
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Environment-Konfiguration**
   - Verwenden Sie niemals Default-Credentials in Produktion
   - Setzen Sie `ENVIRONMENT=production` für Produktionsumgebungen
   - Deaktivieren Sie `DEBUG=false` in Produktion

3. **Datenbank-Sicherheit**
   - Verwenden Sie starke Passwörter für alle Datenbankverbindungen
   - Konfigurieren Sie SSL/TLS für Datenbankverbindungen
   - Implementieren Sie regelmäßige Backups

4. **Netzwerk-Sicherheit**
   - Konfigurieren Sie Firewall-Regeln
   - Verwenden Sie HTTPS in Produktion
   - Beschränken Sie CORS-Origins auf spezifische Domains

### Sicherheitsvalidierung
```bash
# Vollständige Sicherheitsprüfung
python scripts/validate_env.py

# Nur Setup-Anweisungen anzeigen
python scripts/validate_env.py --setup
```

## 📋 Features

- **Tool Registry**: Zentrale Verwaltung von MCP-Tools
- **Composition Engine**: Automatische Tool-Komposition
- **Admin Interface**: Streamlit-basierte Verwaltung
- **API Versioning**: Umfassendes Versioning-System mit Backward Compatibility
- **MCP Transport**: WebSocket, HTTP und stdio Transport-Layer
- **Streaming Support**: Bidirektionale Kommunikation und Streaming-Antworten
- **Security**: JWT-Auth, OPA-Policies, Rate Limiting, Input Validation
- **Monitoring**: Prometheus, Grafana, Logging
- **Enhanced Security**: SQL Injection Protection, XSS Protection, Path Traversal Protection
- **Analytics**: Erweiterte Analytics und Performance-Metriken (v2)

## 🏗️ Architektur

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Clients   │  │   Admin     │  │   API       │
│   (CLI/Web) │  │   Interface │  │   Gateway   │
└─────────────┘  └─────────────┘  └─────────────┘
                          │               │
                    ┌─────────────────────────┐
                    │      MetaMCP Core       │
                    │  Services │ Utils       │
                    │  Auth     │ Monitoring  │
                    │  Tools    │ Security    │
                    │  Version  │ Analytics   │
                    │  Manager  │ (v2)        │
                    └─────────────────────────┘
                          │
                    ┌─────────────────────────┐
                    │    MCP Transport Layer  │
                    │  WebSocket │ HTTP       │
                    │  stdio     │ Streaming  │
                    └─────────────────────────┘
```

## 🔧 Konfiguration

### Umgebungsvariablen

Kritische Umgebungsvariablen für Produktion:

```bash
# Sicherheit
SECRET_KEY=your_secure_secret_key_here_must_be_at_least_32_characters
ENVIRONMENT=production
DEBUG=false

# Datenbank
DATABASE_URL=postgresql://user:secure_password@localhost/metamcp
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# CORS (Produktion)
CORS_ORIGINS=["https://yourdomain.com", "https://admin.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
RATE_LIMIT_USE_REDIS=true

# API Versioning
API_DEFAULT_VERSION=v1
API_LATEST_VERSION=v2

# MCP Transport
MCP_STDIO_ENABLED=true
MCP_STREAMING_ENABLED=true
MCP_WEBSOCKET_PORT=8080
```

### Produktions-Deployment

1. **Sichere Konfiguration**
   ```bash
   # Environment validieren
   python scripts/validate_env.py
   
   # Fehler beheben, falls vorhanden
   ```

2. **Docker Production Build**
   ```bash
   # Production Image bauen
   docker build --target production -t metamcp:production .
   
   # Mit sicheren Umgebungsvariablen starten
   docker run -d \
     --name metamcp \
     -p 9000:8000 \
     --env-file .env.production \
     metamcp:production
   ```

3. **Monitoring Setup**
   ```bash
   # Monitoring Stack starten
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

## 📚 Dokumentation

- [API Versioning](docs/api-versioning.md) - Umfassendes API Versioning System
- [MCP Transport Implementation](docs/mcp-transport-implementation.md) - Transport-Layer Features
- [Admin Interface](docs/admin-interface.md) - Verwaltungsoberfläche
- [API Reference](docs/api.md) - Endpunkt-Dokumentation
- [Configuration](docs/configuration.md) - Einstellungen
- [Development](docs/development.md) - Entwickler-Guide
- [Security Guide](docs/security.md) - Sicherheitsrichtlinien

## 🧪 Tests

```bash
# Alle Tests ausführen
pytest tests/

# Spezifische Test-Kategorien
pytest tests/unit/          # Unit Tests
pytest tests/integration/   # Integration Tests
pytest tests/blackbox/      # End-to-End Tests
pytest tests/ -m security   # Security Tests
pytest tests/unit/api/test_versioning.py  # API Versioning Tests

# MCP Transport Tests
pytest tests/blackbox/mcp_api/test_protocol.py::TestMCPConcurrency -v  # Concurrency Tests
pytest tests/blackbox/mcp_api/test_protocol.py::TestMCPStress -v       # Stress Tests

# Stdio Transport Tests
python scripts/test_stdio_mcp.py

# Test-Coverage
pytest --cov=metamcp --cov-report=html
```

## 🔍 Monitoring

### Health Checks
```bash
# API Health Check
curl http://localhost:9000/health

# Version-spezifische Health Checks
curl http://localhost:9000/api/v1/health
curl http://localhost:9000/api/v2/health

# MCP Transport Health Check
curl http://localhost:9000/mcp/health

# Metrics
curl http://localhost:9000/metrics
```

### Logs
```bash
# Application Logs
docker logs metamcp-server

# Monitoring Logs
docker logs prometheus
docker logs grafana

# MCP Transport Logs
docker logs metamcp-server | grep "MCP\|stdio\|websocket"
```

## 🚨 Sicherheitswarnungen

⚠️ **Wichtige Sicherheitshinweise:**

1. **Ändern Sie IMMER die Default-Credentials** vor dem Deployment
2. **Verwenden Sie HTTPS** in Produktionsumgebungen
3. **Konfigurieren Sie Firewall-Regeln** für alle Services
4. **Implementieren Sie regelmäßige Backups** der Datenbank
5. **Überwachen Sie Logs** auf verdächtige Aktivitäten
6. **Halten Sie alle Dependencies aktuell** mit Sicherheitsupdates
7. **Verwenden Sie die neueste API-Version** für neue Entwicklungen
8. **Konfigurieren Sie Transport-Sicherheit** für MCP-Verbindungen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

## 🤝 Beitragen

Bitte lesen Sie unsere [Contributing Guidelines](CONTRIBUTING.md) und [Security Policy](SECURITY.md) bevor Sie Beiträge leisten.