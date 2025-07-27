# Admin Interface

Streamlit-basierte Verwaltungsoberfläche für MetaMCP.

## 🚀 Start

```bash
# Direkt
python scripts/start_admin.py

# Streamlit
streamlit run metamcp/admin/streamlit_app.py --server.port 9501

# Docker
docker-compose up metamcp-admin
```

**URL:** http://localhost:9501

## 📊 Funktionen

### Dashboard
- System-Übersicht (Uptime, Version)
- Live-Metriken (Memory, CPU, Disk)
- Error-Tracking
- Aktivitäts-Logs

### User Management
- User-Liste mit Pagination
- Filtering (Username, Email, Rolle, Status)
- CRUD-Operationen (Erstellen, Bearbeiten, Löschen)
- Rollen-Management

### Tool Management
- Tool-Registry
- Status-Monitoring
- Usage-Statistiken
- Tool-Konfiguration

### System Monitoring
- Real-time Metriken
- Health-Indikatoren
- System-Informationen

### Logs
- System-Logs mit Level-Filtering
- Log-Statistiken
- Real-time Updates

### System Control
- System-Restart
- Konfiguration anzeigen
- Health-Check

## 🔧 Konfiguration

```bash
# .env
ADMIN_ENABLED=true
ADMIN_PORT=9501
ADMIN_API_URL=http://localhost:8000/api/v1/admin/
ADMIN_AUTO_REFRESH_INTERVAL=30000
```

## 🏗️ Architektur

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

## 🧪 Tests

```bash
pytest tests/unit/admin/ -v
```

## 🔒 Sicherheit

- **Admin-Only Access**: Nur für Administratoren
- **JWT-Authentication**: Token-basierte Authentifizierung
- **Role-Based Access**: Granulare Berechtigungen
- **Action-Auditing**: Protokollierung aller Aktionen

## 🚀 Deployment

### Production
```bash
# Environment konfigurieren
export ADMIN_ENABLED=true
export ADMIN_API_URL=http://backend:8000/api/v1/admin/

# Starten
docker run -d -p 9501:9501 metamcp-admin
```

### Kubernetes
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

### Admin Interface startet nicht
```bash
# Logs prüfen
docker logs metamcp-admin

# Konfiguration prüfen
echo $ADMIN_ENABLED
echo $ADMIN_API_URL
```

### API-Verbindung fehlschlägt
```bash
# Backend-Verfügbarkeit prüfen
curl http://localhost:8000/api/v1/admin/health
```

## 📈 Monitoring

- **Response Times**: API-Antwortzeiten
- **Error Rates**: Fehlerquoten
- **User Activity**: Admin-Interface-Nutzung
- **System Performance**: Memory, CPU Usage