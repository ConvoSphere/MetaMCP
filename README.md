# MetaMCP

**Meta Model Context Protocol** - Ein modulares System für Tool-Komposition und MCP-Management.

## 🚀 Schnellstart

### Installation
```bash
git clone https://github.com/metamcp/metamcp.git
cd metamcp
pip install -r requirements.txt
```

### Start
```bash
# Backend
python -m metamcp.main

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

## 📋 Features

- **Tool Registry**: Zentrale Verwaltung von MCP-Tools
- **Composition Engine**: Automatische Tool-Komposition
- **Admin Interface**: Streamlit-basierte Verwaltung
- **Security**: JWT-Auth, OPA-Policies, Rate Limiting
- **Monitoring**: Prometheus, Grafana, Logging

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
                    └─────────────────────────┘
```

## 📚 Dokumentation

- [Admin Interface](docs/admin-interface.md) - Verwaltungsoberfläche
- [API Reference](docs/api.md) - Endpunkt-Dokumentation
- [Configuration](docs/configuration.md) - Einstellungen
- [Development](docs/development.md) - Entwickler-Guide

## 🧪 Tests

```bash
pytest tests/unit/          # Unit Tests
pytest tests/integration/   # Integration Tests
pytest tests/blackbox/      # End-to-End Tests
```

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.