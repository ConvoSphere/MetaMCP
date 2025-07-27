# MetaMCP Admin Interface

Das MetaMCP Admin Interface ist eine Streamlit-basierte Weboberfläche zur Verwaltung des MetaMCP-Systems. Es kommuniziert ausschließlich über die Admin-API und bietet eine saubere Trennung zwischen Frontend und Backend.

## 🏗️ Architektur

### Saubere Trennung
- **Admin-API**: Einzige Kommunikationsschnittstelle für das Admin-Interface
- **Streamlit Frontend**: Reine Präsentationsschicht ohne direkte Datenbankzugriffe
- **RESTful API**: Vollständige CRUD-Operationen für alle Admin-Funktionen

### Komponenten
```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Streamlit     │ ──────────────► │   Admin API     │
│   Frontend      │                 │   (FastAPI)     │
└─────────────────┘                 └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   Services      │
                                    │   (Auth, Tools) │
                                    └─────────────────┘
```

## 🚀 Installation und Start

### Voraussetzungen
- Python 3.8+
- MetaMCP Backend läuft auf Port 8000
- Streamlit Dependencies installiert

### Dependencies installieren
```bash
pip install -r requirements.txt
```

### Admin Interface starten

#### Option 1: Direkter Start
```bash
python scripts/start_admin.py
```

#### Option 2: Streamlit direkt
```bash
streamlit run metamcp/admin/streamlit_app.py --server.port 9501
```

#### Option 3: Docker Compose
```bash
docker-compose up metamcp-admin
```

### Konfiguration
Die Admin-Interface-Konfiguration erfolgt über Umgebungsvariablen:

```bash
# Admin Interface Settings
ADMIN_ENABLED=true
ADMIN_PORT=9501
ADMIN_API_URL=http://localhost:8000/api/v1/admin/
ADMIN_AUTO_REFRESH_INTERVAL=30000
```

## 📊 Funktionen

### 1. Dashboard
- **System-Übersicht**: Uptime, Version, Environment
- **Live-Metriken**: Memory, CPU, Disk Usage, Active Connections
- **Error-Tracking**: Fehlerstatistiken und Trends
- **Aktivitäts-Logs**: Letzte Systemaktivitäten

### 2. User Management
- **User-Liste**: Paginierte Anzeige aller Benutzer
- **Filtering**: Suche nach Username, Email, Rolle, Status
- **CRUD-Operationen**: Erstellen, Bearbeiten, Löschen von Benutzern
- **Rollen-Management**: Zuweisung von Rollen und Berechtigungen

### 3. Tool Management
- **Tool-Registry**: Übersicht aller registrierten Tools
- **Status-Monitoring**: Tool-Status und Health-Checks
- **Usage-Statistiken**: Nutzungszahlen und Error-Rates
- **Tool-Konfiguration**: Endpoint-URLs, Schemas, Auth-Types

### 4. System Monitoring
- **Real-time Metriken**: Live-System-Performance
- **Health-Indikatoren**: Memory, CPU, Disk Usage Gauge-Charts
- **System-Informationen**: Version, Environment, Start-Zeit
- **Performance-Trends**: Historische Daten (geplant)

### 5. Logs
- **System-Logs**: Strukturierte Log-Anzeige
- **Level-Filtering**: Filter nach Log-Level (DEBUG, INFO, WARNING, ERROR)
- **Log-Statistiken**: Verteilung nach Log-Level
- **Real-time Updates**: Automatische Aktualisierung

### 6. System Control
- **System-Restart**: Neustart des gesamten Systems
- **Konfiguration**: Anzeige der aktuellen System-Konfiguration
- **Health-Check**: System-Status und Service-Health
- **Warnungen**: Sichere Ausführung kritischer Operationen

## 🔧 API-Endpunkte

Das Admin-Interface nutzt folgende API-Endpunkte:

### Dashboard & Overview
- `GET /api/v1/admin/dashboard` - Komplette Dashboard-Daten
- `GET /api/v1/admin/system/metrics` - System-Metriken
- `GET /api/v1/admin/config` - System-Konfiguration

### User Management
- `GET /api/v1/admin/users` - User-Liste mit Pagination
- `POST /api/v1/admin/users` - Neuen User erstellen
- `GET /api/v1/admin/users/{user_id}` - User-Details
- `PUT /api/v1/admin/users/{user_id}` - User aktualisieren
- `DELETE /api/v1/admin/users/{user_id}` - User löschen

### Tool Management
- `GET /api/v1/admin/tools` - Tool-Liste mit Pagination
- `POST /api/v1/admin/tools` - Neues Tool erstellen
- `GET /api/v1/admin/tools/{tool_id}` - Tool-Details
- `PUT /api/v1/admin/tools/{tool_id}` - Tool aktualisieren
- `DELETE /api/v1/admin/tools/{tool_id}` - Tool löschen

### System Management
- `GET /api/v1/admin/logs` - System-Logs
- `POST /api/v1/admin/system/restart` - System-Neustart
- `GET /api/v1/admin/health` - Health-Check

## 🎨 UI/UX Features

### Responsive Design
- **Mobile-First**: Optimiert für alle Bildschirmgrößen
- **Grid-Layout**: Flexible Karten-basierte Darstellung
- **Sidebar-Navigation**: Intuitive Navigation zwischen Bereichen

### Interaktive Elemente
- **Auto-Refresh**: Automatische Aktualisierung alle 30 Sekunden
- **Real-time Charts**: Plotly-basierte Gauge-Charts und Visualisierungen
- **Form-Validation**: Client-seitige Validierung aller Eingaben
- **Success/Error Messages**: Klare Feedback-Mechanismen

### Datenvisualisierung
- **Gauge-Charts**: Memory, CPU, Disk Usage
- **Pie-Charts**: Log-Verteilung nach Level
- **DataTables**: Sortierbare und filterbare Tabellen
- **Status-Indikatoren**: Farbkodierte Status-Anzeigen

## 🔒 Sicherheit

### Authentifizierung
- **Admin-Only Access**: Nur für Administratoren zugänglich
- **API-Authentication**: JWT-basierte Authentifizierung
- **Session-Management**: Sichere Session-Verwaltung

### Autorisierung
- **Role-Based Access**: Granulare Berechtigungen
- **Action-Auditing**: Protokollierung aller Admin-Aktionen
- **Safe Operations**: Bestätigung für kritische Operationen

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/admin/ -v
```

### Integration Tests
```bash
pytest tests/integration/admin/ -v
```

### E2E Tests
```bash
pytest tests/blackbox/rest_api/test_admin.py -v
```

## 🚀 Deployment

### Production Setup
1. **Environment Variables** konfigurieren
2. **SSL/TLS** für HTTPS einrichten
3. **Reverse Proxy** (nginx) konfigurieren
4. **Monitoring** und **Logging** aktivieren

### Docker Deployment
```bash
# Production Build
docker build -t metamcp-admin .

# Run with environment
docker run -d \
  -p 9501:9501 \
  -e ADMIN_API_URL=http://backend:8000/api/v1/admin/ \
  -e ADMIN_ENABLED=true \
  metamcp-admin
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamcp-admin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metamcp-admin
  template:
    metadata:
      labels:
        app: metamcp-admin
    spec:
      containers:
      - name: admin
        image: metamcp-admin:latest
        ports:
        - containerPort: 9501
        env:
        - name: ADMIN_API_URL
          value: "http://metamcp-server:8000/api/v1/admin/"
```

## 🔧 Troubleshooting

### Häufige Probleme

#### Admin Interface startet nicht
```bash
# Prüfen Sie die Logs
docker logs metamcp-admin

# Prüfen Sie die Konfiguration
echo $ADMIN_ENABLED
echo $ADMIN_API_URL
```

#### API-Verbindung fehlschlägt
```bash
# Prüfen Sie die Backend-Verfügbarkeit
curl http://localhost:8000/api/v1/admin/health

# Prüfen Sie die Netzwerk-Konfiguration
docker network ls
docker network inspect metamcp-network
```

#### Streamlit-Fehler
```bash
# Dependencies prüfen
pip list | grep streamlit

# Streamlit-Cache leeren
streamlit cache clear
```

### Debug-Modus
```bash
# Streamlit im Debug-Modus starten
STREAMLIT_DEBUG=true streamlit run metamcp/admin/streamlit_app.py
```

## 📈 Monitoring

### Metriken
- **Response Times**: API-Antwortzeiten
- **Error Rates**: Fehlerquoten der Admin-API
- **User Activity**: Admin-Interface-Nutzung
- **System Performance**: Memory, CPU Usage

### Logs
- **Access Logs**: Admin-Interface-Zugriffe
- **Error Logs**: Fehler und Exceptions
- **Audit Logs**: Admin-Aktionen und Änderungen

## 🔮 Roadmap

### Geplante Features
- [ ] **Real-time Notifications**: WebSocket-basierte Benachrichtigungen
- [ ] **Advanced Analytics**: Detaillierte Performance-Analysen
- [ ] **Bulk Operations**: Massenbearbeitung von Users/Tools
- [ ] **Export/Import**: Daten-Export und -Import
- [ ] **Custom Dashboards**: Benutzerdefinierte Dashboard-Widgets
- [ ] **Multi-language Support**: Internationalisierung
- [ ] **Dark Mode**: Dunkles Theme
- [ ] **Keyboard Shortcuts**: Tastaturkürzel für Power-User

### Performance-Optimierungen
- [ ] **Caching**: Client-seitiges Caching für bessere Performance
- [ ] **Lazy Loading**: Nachladung von Daten bei Bedarf
- [ ] **Virtual Scrolling**: Für große Datenmengen
- [ ] **Progressive Loading**: Schrittweise Datenladung

## 📚 Weitere Ressourcen

- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Admin API](api/admin.md)
- [MetaMCP Configuration](configuration.md)
- [Development Guide](developer-guide.md)