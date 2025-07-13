# Black Box Tests für MetaMCP

Diese Tests behandeln den MetaMCP Container als Black Box und testen nur über die öffentlichen Schnittstellen (REST API und MCP Protokoll).

## Test-Organisation

```
tests/blackbox/
├── __init__.py                 # Hauptmodul
├── conftest.py                 # Gemeinsame Fixtures und Utilities
├── README.md                   # Diese Datei
├── rest_api/                   # REST API Tests
│   ├── __init__.py
│   ├── test_auth.py           # Authentifizierung Tests
│   ├── test_tools.py          # Tool Management Tests
│   └── test_health.py         # Health Monitoring Tests
├── mcp_api/                    # MCP Protokoll Tests
│   ├── __init__.py
│   └── test_protocol.py       # MCP WebSocket Tests
├── integration/                # Integration Tests
│   ├── __init__.py
│   └── test_workflows.py      # Komplexe Workflow Tests
└── performance/                # Performance Tests
    ├── __init__.py
    └── test_load.py           # Load und Stress Tests
```

## Test-Kategorien

### REST API Tests (`rest_api/`)
- **Authentifizierung**: Login, Logout, Token Refresh, Berechtigungen
- **Tool Management**: Registrierung, Ausführung, Suche, CRUD Operationen
- **Health Monitoring**: Health Checks, Readiness, Liveness Probes

### MCP API Tests (`mcp_api/`)
- **Protokoll Tests**: WebSocket Verbindung, MCP Initialisierung
- **Tool Integration**: Tool Listing und Execution über MCP
- **Error Handling**: Fehlerbehandlung für ungültige Anfragen

### Integration Tests (`integration/`)
- **Cross-API Workflows**: Tests über REST und MCP APIs
- **Authentifizierung Workflows**: Token-Konsistenz über APIs
- **Error Handling**: Fehlerbehandlung in komplexen Szenarien
- **Data Consistency**: Datenkonsistenz über verschiedene Operationen

### Performance Tests (`performance/`)
- **Response Time**: Antwortzeiten für verschiedene Endpunkte
- **Concurrent Load**: Gleichzeitige Anfragen
- **Stress Testing**: Rapid Requests, Large Payloads
- **Resource Utilization**: Connection Pool, Memory Usage

## Ausführung

### Voraussetzungen
- MetaMCP Container läuft auf `localhost:8000`
- Python Dependencies installiert (pytest, httpx, websockets)

### Alle Tests ausführen
```bash
pytest tests/blackbox/ -v
```

### Spezifische Test-Kategorien
```bash
# Nur REST API Tests
pytest tests/blackbox/rest_api/ -v

# Nur MCP API Tests
pytest tests/blackbox/mcp_api/ -v

# Nur Integration Tests
pytest tests/blackbox/integration/ -v

# Nur Performance Tests
pytest tests/blackbox/performance/ -v
```

### Mit Service-Wait
```bash
# Warten bis Service bereit ist
python -c "from tests.blackbox.conftest import wait_for_service; wait_for_service()"
pytest tests/blackbox/ -v
```

## Test-Konfiguration

### Umgebungsvariablen
- `BASE_URL`: MetaMCP Service URL (Standard: `http://localhost:8000`)
- `API_BASE_URL`: REST API Base URL (Standard: `http://localhost:8000/api/v1`)
- `WS_URL`: WebSocket URL für MCP (Standard: `ws://localhost:8000/mcp/ws`)

### Test-Daten
- `TEST_USER`: Standard Test-Benutzer
- `TEST_TOOL`: Standard Test-Tool Definition

## Test-Fixtures

### HTTP Client
- `http_client`: Basis HTTP Client
- `authenticated_client`: HTTP Client mit Auth Token

### WebSocket
- `websocket_connection`: MCP WebSocket Verbindung

### Test-Daten
- `test_tool_id`: Registriertes Test-Tool mit Cleanup

## Assertion Utilities

### `assert_success_response(response, expected_status=200)`
Prüft erfolgreiche HTTP Responses und gibt JSON Data zurück.

### `assert_error_response(response, expected_status, expected_error=None)`
Prüft Error HTTP Responses und gibt Error Data zurück.

## Test-Strategien

### Black Box Ansatz
- Keine internen APIs oder Datenbankzugriffe
- Tests nur über öffentliche Schnittstellen
- Realistische Benutzer-Szenarien

### Isolation
- Jeder Test ist unabhängig
- Automatisches Cleanup nach Tests
- Keine Test-Abhängigkeiten

### Robustheit
- Graceful Error Handling
- Timeout Protection
- Connection Recovery

## Monitoring und Debugging

### Logs aktivieren
```bash
pytest tests/blackbox/ -v --log-cli-level=DEBUG
```

### Einzelne Tests debuggen
```bash
pytest tests/blackbox/rest_api/test_auth.py::TestAuthentication::test_login_success -v -s
```

### Performance Profiling
```bash
pytest tests/blackbox/performance/ -v --durations=10
```

## CI/CD Integration

### GitHub Actions Beispiel
```yaml
- name: Run Black Box Tests
  run: |
    # Start MetaMCP Container
    docker-compose up -d
    
    # Wait for service
    python -c "from tests.blackbox.conftest import wait_for_service; wait_for_service()"
    
    # Run tests
    pytest tests/blackbox/ -v --junitxml=blackbox-results.xml
```

### Test Reports
- JUnit XML Reports für CI
- Performance Metrics
- Error Classification

## Wartung

### Neue Tests hinzufügen
1. Wähle passende Kategorie (rest_api, mcp_api, integration, performance)
2. Erstelle neue Test-Datei oder erweitere bestehende
3. Nutze vorhandene Fixtures und Utilities
4. Füge Cleanup-Logik hinzu

### Test-Daten aktualisieren
- Bearbeite `conftest.py` für globale Test-Daten
- Aktualisiere Test-spezifische Daten in den Test-Dateien

### Performance Thresholds anpassen
- Bearbeite Timeout-Werte in Performance Tests
- Passe Load-Test Parameter an
- Aktualisiere Assertion-Schwellenwerte

## Troubleshooting

### Häufige Probleme

**Service nicht erreichbar**
```bash
# Prüfe Container Status
docker-compose ps

# Prüfe Logs
docker-compose logs metamcp
```

**Timeout Fehler**
- Erhöhe Timeout-Werte in `conftest.py`
- Prüfe Service Performance
- Reduziere Concurrent Load in Tests

**Authentication Fehler**
- Prüfe Test-Benutzer Konfiguration
- Stelle sicher, dass Auth-Service läuft
- Prüfe Token-Validierung

**WebSocket Verbindungsfehler**
- Prüfe MCP Service Status
- Stelle sicher, dass WebSocket Port offen ist
- Prüfe Firewall-Einstellungen 