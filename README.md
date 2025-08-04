# MetaMCP

**Meta Model Context Protocol** - Ein modulares System für Tool-Komposition und MCP-Management.

## 🚀 Schnellstart

### Installation
```bash
git clone https://github.com/metamcp/metamcp.git
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
- **Security**: JWT-Auth, OPA-Policies, Rate Limiting, Input Validation
- **Monitoring**: Prometheus, Grafana, Logging
- **Enhanced Security**: SQL Injection Protection, XSS Protection, Path Traversal Protection

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

# Test-Coverage
pytest --cov=metamcp --cov-report=html
```

## 🔍 Monitoring

### Health Checks
```bash
# API Health Check
curl http://localhost:9000/health

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
```

## 🚨 Sicherheitswarnungen

⚠️ **Wichtige Sicherheitshinweise:**

1. **Ändern Sie IMMER die Default-Credentials** vor dem Deployment
2. **Verwenden Sie HTTPS** in Produktionsumgebungen
3. **Konfigurieren Sie Firewall-Regeln** für alle Services
4. **Implementieren Sie regelmäßige Backups** der Datenbank
5. **Überwachen Sie Logs** auf verdächtige Aktivitäten
6. **Halten Sie alle Dependencies aktuell** mit Sicherheitsupdates

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

## 🤝 Beitragen

Bitte lesen Sie unsere [Contributing Guidelines](CONTRIBUTING.md) und [Security Policy](SECURITY.md) bevor Sie Beiträge leisten.