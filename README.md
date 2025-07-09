# MCP Meta-Server

Ein Open-Source MCP Meta-Server als dynamischer Tool-Proxy für AI-Agenten nach dem Model Context Protocol (MCP).

## 🎯 Überblick

Der MCP Meta-Server fungiert als intelligenter Proxy und Tool-Registry für AI-Agenten. Er ermöglicht es AI-Agenten, Aufgaben zu beschreiben und erhält daraufhin eine Auswahl der am besten geeigneten Tools (MCP-kompatible Server) inklusive Nutzungsanweisungen zurück. Die Tool-Auswahl erfolgt dynamisch über semantische Suche mit Embeddings.

## ✨ Features

### Core Features
- **MCP-Kompatibilität**: Vollständige Implementierung des Model Context Protocol
- **Tool-Registry**: Dynamische Verwaltung von Tools mit Metadaten und Beschreibungen
- **Semantische Suche**: KI-basierte Tool-Auswahl über Vektor-Embeddings mit Weaviate
- **Proxy & Orchestrierung**: Intelligente Weiterleitung von Agent-Requests an passende Tools
- **Security & Policies**: Rollen-/Rechteverwaltung und Audit-Logging
- **LLM-Integration**: Automatische Tool-Beschreibungsgenerierung

### Enterprise Features
- **Policy Engine**: OPA-Integration für granulare Zugriffskontrolle
- **Audit Logging**: Vollständige Nachverfolgung aller Requests
- **Admin UI**: Web-Interface für Tool-Management
- **OpenAPI Integration**: Automatische Tool-Import von Swagger-Specs

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agents (MCP Clients)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────▼───────────────────────────────────────┐
│                  MCP Meta-Server                            │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  │   FastAPI   │ │   FastMCP    │ │   Security Layer    │   │
│  │   REST API  │ │   Server     │ │   (OPA/Policies)    │   │
│  └─────────────┘ └──────────────┘ └─────────────────────┘   │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  │Tool Registry│ │   Semantic   │ │    LLM Service      │   │
│  │  Database   │ │    Search    │ │  (Embeddings/Gen)   │   │
│  │             │ │  (Weaviate)  │ │                     │   │
│  └─────────────┘ └──────────────┘ └─────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ Tool-specific Protocols
┌─────────────────────▼───────────────────────────────────────┐
│              Registered MCP Tools/Services                  │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  │    Tool A   │ │    Tool B    │ │      Tool C         │   │
│  │ (Database)  │ │  (Web API)   │ │  (File System)      │   │
│  └─────────────┘ └──────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Mit Docker Compose (Empfohlen)

```bash
# Repository klonen
git clone https://github.com/your-org/MetaMCP.git
cd MetaMCP

# Services starten
docker-compose up -d

# Admin UI öffnen
open http://localhost:8080
```

### Entwicklungsumgebung

```bash
# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
cp .env.example .env
# .env editieren mit Ihren Einstellungen

# Weaviate starten
docker-compose up -d weaviate

# Server starten
python -m metamcp.main
```

## 📋 Anforderungen

### System Requirements
- Python 3.8+
- Docker & Docker Compose
- 4GB RAM (für Weaviate)

### Optional
- NVIDIA GPU (für lokale LLM-Modelle)
- OpenAI API Key (für Online-LLMs)

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/metamcp

# Weaviate
WEAVIATE_URL=http://localhost:8088
WEAVIATE_API_KEY=optional_api_key

# LLM Provider
LLM_PROVIDER=openai  # oder ollama, huggingface
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434

# Security
SECRET_KEY=your-secret-key
OPA_URL=http://localhost:8181

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_ENABLED=true
```

### Policy Konfiguration

Policies werden in `policies/` als Rego-Dateien für OPA definiert:

```rego
# policies/tool_access.rego
package metamcp.tools

default allow = false

allow {
    input.user.role == "admin"
}

allow {
    input.user.role == "agent"
    input.tool.security_level <= input.user.clearance_level
}
```

## 📚 API Dokumentation

### MCP Protocol Endpoints

Der Server implementiert das vollständige MCP-Protokoll:

- `POST /mcp/initialize` - Client-Initialisierung
- `POST /mcp/tools/list` - Verfügbare Tools auflisten
- `POST /mcp/tools/call` - Tool-Ausführung
- `POST /mcp/resources/list` - Ressourcen auflisten

### REST API Endpoints

Management API für Tool-Registry:

- `GET /api/v1/tools` - Tools auflisten
- `POST /api/v1/tools` - Tool registrieren
- `PUT /api/v1/tools/{id}` - Tool aktualisieren
- `DELETE /api/v1/tools/{id}` - Tool löschen
- `POST /api/v1/tools/search` - Semantische Tool-Suche

Vollständige API-Dokumentation: http://localhost:8000/docs

## 🛡️ Sicherheit

### Authentifizierung
- JWT-basierte Authentifizierung für API-Zugriff
- MCP-Session-Management für Agent-Verbindungen

### Autorisierung
- Role-Based Access Control (RBAC)
- Policy-basierte Zugriffskontrolle mit OPA
- Tool-spezifische Berechtigungen

### Audit & Compliance
- Vollständiges Audit-Logging aller Requests
- Policy-Evaluation Logging
- Performance Metriken und Monitoring

## 🔌 Tool-Integration

### Tool registrieren

```python
from metamcp.client import MetaMCPClient

client = MetaMCPClient("http://localhost:8000")

tool = {
    "name": "database_query",
    "description": "Query SQL databases with natural language",
    "category": "database",
    "endpoint": "http://db-tool:8001",
    "security_level": 2,
    "capabilities": ["read", "analyze"],
    "schema": {
        "input": {"query": "string"},
        "output": {"results": "array"}
    }
}

client.register_tool(tool)
```

### Tool verwenden (von AI-Agent)

```python
import asyncio
from mcp.client import MCPClient

async def use_tools():
    client = MCPClient("ws://localhost:8000/mcp")
    await client.connect()
    
    # Tools für Aufgabe finden
    task = "Analyze sales data from the last quarter"
    tools = await client.search_tools(task)
    
    # Bestes Tool auswählen und verwenden
    best_tool = tools[0]
    result = await client.call_tool(
        best_tool["name"], 
        {"query": task}
    )
    
    print(result)

asyncio.run(use_tools())
```

## 🧪 Testing

```bash
# Unit Tests
pytest tests/unit/

# Integration Tests
pytest tests/integration/

# E2E Tests
pytest tests/e2e/

# Performance Tests
pytest tests/performance/

# Coverage Report
pytest --cov=metamcp --cov-report=html
```

## 📊 Monitoring & Observability

### Metriken
- Request Latency & Throughput
- Tool-Usage Statistics
- Embedding-Qualität Metriken
- Policy-Evaluation Performance

### Health Checks
- `GET /health` - Service Health
- `GET /health/weaviate` - Weaviate Connectivity
- `GET /health/llm` - LLM Service Status

### Logging
Strukturierte Logs in JSON-Format mit konfigurierbaren Log-Levels.

## 🚀 Deployment

### Production Setup

```bash
# Mit Docker Swarm
docker stack deploy -c docker-stack.yml metamcp

# Mit Kubernetes
kubectl apply -f k8s/

# Mit Terraform
cd terraform/
terraform apply
```

### Umgebungen
- **Development**: Single-Node Docker Compose
- **Staging**: Multi-Node mit Load Balancer
- **Production**: Kubernetes mit Auto-Scaling

## 🤝 Contributing

1. Fork das Repository
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Changes committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

### Development Guidelines
- Code Style: Black + isort
- Type Hints: mypy compliance
- Documentation: Docstrings für alle Public APIs
- Testing: Minimum 80% Coverage

## 📄 Lizenz

Dieses Projekt ist unter der MIT License lizensiert - siehe [LICENSE](LICENSE) für Details.

## 📞 Support

- **Dokumentation**: [Wiki](https://github.com/your-org/MetaMCP/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/MetaMCP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/MetaMCP/discussions)
- **Community**: [Discord](https://discord.gg/metamcp)

## 🗺️ Roadmap

### Version 1.0 (MVP)
- [x] MCP Protocol Implementation
- [x] Basic Tool Registry
- [x] Semantic Search with Weaviate
- [x] Simple Security Layer
- [x] Docker Compose Setup

### Version 1.1
- [ ] Admin Web UI
- [ ] OpenAPI Tool Import
- [ ] Advanced Policy Engine
- [ ] Performance Optimizations

### Version 2.0
- [ ] Multi-tenancy Support
- [ ] GraphQL API
- [ ] Real-time Tool Monitoring
- [ ] ML-based Tool Recommendation

---

**Made with ❤️ by the MetaMCP Community**