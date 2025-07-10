# Production Setup

This guide covers the production deployment of MetaMCP with comprehensive monitoring and observability.

## Overview

Production deployment includes:

- **Application**: MetaMCP server with telemetry enabled
- **Monitoring Stack**: Prometheus, Grafana, Jaeger, AlertManager
- **Infrastructure**: Docker/Kubernetes deployment
- **Security**: TLS, authentication, network policies
- **Scaling**: Load balancing, horizontal scaling

## Prerequisites

### System Requirements

- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: Stable internet connection
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+
- PostgreSQL 13+
- Redis 6+ (optional)

## Deployment Options

### Option 1: Docker Compose (Recommended for small-medium deployments)

```bash
# Clone repository
git clone https://github.com/your-org/metamcp.git
cd metamcp

# Create environment file
cp .env.example .env
# Edit .env with production values

# Start monitoring stack
./scripts/start-monitoring.sh

# Start application
docker-compose up -d
```

### Option 2: Kubernetes

```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metamcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: metamcp
  template:
    metadata:
      labels:
        app: metamcp
    spec:
      containers:
      - name: metamcp
        image: metamcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: TELEMETRY_ENABLED
          value: "true"
        - name: OTLP_ENDPOINT
          value: "http://otel-collector:4317"
```

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=MetaMCP
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@db:5432/metamcp
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Vector Database
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=your-api-key

# LLM
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4

# Security
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Telemetry
TELEMETRY_ENABLED=true
OTLP_ENDPOINT=http://otel-collector:4317
OTLP_INSECURE=false
PROMETHEUS_METRICS_PORT=9090

# Monitoring
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Security Configuration

```bash
# TLS/SSL
SSL_CERT_FILE=/path/to/cert.pem
SSL_KEY_FILE=/path/to/key.pem

# Authentication
AUTH_ENABLED=true
AUTH_PROVIDER=ldap  # or oauth, saml

# Network
ALLOWED_HOSTS=metamcp.example.com
CORS_ORIGINS=https://app.example.com
```

## Monitoring Setup

### 1. Start Monitoring Stack

```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Configure Grafana

1. Access Grafana: http://your-server:3000
2. Login with admin/admin
3. Add Prometheus data source
4. Import MetaMCP dashboard

### 3. Configure Alerts

```yaml
# monitoring/alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR_WEBHOOK'

route:
  receiver: 'slack.critical'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty.critical'
```

## Performance Tuning

### Application Tuning

```python
# config.py
class ProductionSettings(Settings):
    # Performance
    workers = 4
    worker_class = "uvicorn.workers.UvicornWorker"
    max_requests = 1000
    max_requests_jitter = 100
    
    # Database
    database_pool_size = 20
    database_max_overflow = 30
    database_pool_pre_ping = True
    
    # Caching
    cache_ttl = 300
    cache_max_size = 1000
    
    # Rate Limiting
    rate_limit_requests = 1000
    rate_limit_window = 60
```

### Database Tuning

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### Monitoring Tuning

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'metamcp'
    scrape_interval: 10s
    scrape_timeout: 5s
    static_configs:
      - targets: ['metamcp:9090']
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  metamcp:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Load Balancing

```nginx
# nginx.conf
upstream metamcp {
    server metamcp1:8000;
    server metamcp2:8000;
    server metamcp3:8000;
}

server {
    listen 80;
    server_name metamcp.example.com;
    
    location / {
        proxy_pass http://metamcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump $DATABASE_URL > $BACKUP_DIR/metamcp_$DATE.sql

# Weaviate backup
curl -X GET "http://weaviate:8080/v1/backup" \
  -H "Authorization: Bearer $WEAVIATE_API_KEY" \
  -d '{"id": "metamcp_backup_$DATE"}'

# Compress backups
tar -czf $BACKUP_DIR/metamcp_$DATE.tar.gz $BACKUP_DIR/metamcp_$DATE.sql
```

### Monitoring Data Backup

```bash
# Prometheus data
docker run --rm -v prometheus_data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/prometheus_$(date +%Y%m%d).tar.gz -C /data .

# Grafana data
docker run --rm -v grafana_data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/grafana_$(date +%Y%m%d).tar.gz -C /data .
```

## Security Hardening

### Network Security

```bash
# Firewall rules
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # MetaMCP API
ufw allow 9090/tcp  # Prometheus
ufw allow 3000/tcp  # Grafana
ufw enable
```

### Application Security

```python
# security.py
from cryptography.fernet import Fernet

class SecurityManager:
    def __init__(self):
        self.cipher = Fernet(SECRET_KEY)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### Monitoring Security

```yaml
# prometheus.yml
global:
  external_labels:
    cluster: production
    environment: prod

scrape_configs:
  - job_name: 'metamcp'
    tls_config:
      ca_file: /etc/ssl/certs/ca-certificates.crt
    authorization:
      type: Bearer
      credentials: your-prometheus-token
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats metamcp
   
   # Increase memory limits
   docker-compose.yml:
     deploy:
       resources:
         limits:
           memory: 8G
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   docker exec metamcp python -c "
   from metamcp.config import get_settings
   import psycopg2
   settings = get_settings()
   conn = psycopg2.connect(settings.database_url)
   print('Database connection successful')
   "
   ```

3. **Telemetry Issues**
   ```bash
   # Check OTLP connectivity
   curl -X GET http://otel-collector:4317/health
   
   # Check Jaeger
   curl -X GET http://jaeger:16686/api/services
   ```

### Log Analysis

```bash
# Application logs
docker logs metamcp --tail 100

# Monitoring logs
docker logs prometheus --tail 50
docker logs grafana --tail 50
docker logs jaeger --tail 50

# System logs
journalctl -u docker.service -f
```

## Maintenance

### Regular Maintenance Tasks

1. **Database Maintenance**
   ```sql
   -- Weekly
   VACUUM ANALYZE;
   REINDEX DATABASE metamcp;
   ```

2. **Log Rotation**
   ```bash
   # /etc/logrotate.d/metamcp
   /var/log/metamcp/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 metamcp metamcp
   }
   ```

3. **Backup Verification**
   ```bash
   # Test backup restoration
   docker exec -it postgres psql -U metamcp -d metamcp_test -f backup.sql
   ```

### Update Procedures

```bash
# Zero-downtime deployment
docker-compose pull
docker-compose up -d --no-deps --build metamcp

# Rollback procedure
docker-compose up -d --no-deps metamcp:previous-version
```

This production setup provides a robust, scalable, and monitored deployment of MetaMCP with comprehensive observability and security measures. 