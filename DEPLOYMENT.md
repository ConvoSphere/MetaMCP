# MCP Meta-Server Deployment Guide

This guide provides detailed instructions for deploying the MCP Meta-Server in various environments.

## 🚀 Quick Start

### Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/your-org/MetaMCP.git
cd MetaMCP

# 2. Start development environment
./scripts/start-dev.sh
```

The development environment will be available at:
- **API**: http://localhost:8000
- **Admin UI**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs

### Production with Docker Compose

```bash
# 1. Clone and configure
git clone https://github.com/your-org/MetaMCP.git
cd MetaMCP
cp .env.example .env

# 2. Edit .env with production values
vim .env

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database
DATABASE_URL=postgresql://metamcp:password@postgres:5432/metamcp

# Weaviate
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=optional-api-key

# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=["https://yourdomain.com"]

# Policy Engine
OPA_URL=http://opa:8181

# Monitoring
METRICS_ENABLED=true
SENTRY_DSN=https://your-sentry-dsn
```

### Required Secrets

⚠️ **Security**: Always change default secrets in production!

```bash
# Generate secure secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For ADMIN_UI_SECRET_KEY
```

## 🐳 Docker Deployment

### Single Node Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  metamcp-server:
    image: metamcp/server:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://metamcp:${DB_PASSWORD}@postgres:5432/metamcp
      - WEAVIATE_URL=http://weaviate:8080
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
      - weaviate
      - redis
    restart: unless-stopped
    
  # ... other services
```

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-stack.yml metamcp
```

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/api/v1/health/detailed
```

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Helm 3 (optional)

### Using Kubernetes Manifests

```bash
# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/weaviate.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/opa.yaml
kubectl apply -f k8s/metamcp.yaml
```

### Using Helm Chart

```bash
# Add Helm repository
helm repo add metamcp https://charts.metamcp.org
helm repo update

# Install with custom values
helm install metamcp metamcp/metamcp \
  --namespace metamcp \
  --create-namespace \
  --values values.yaml
```

### Example `values.yaml`:

```yaml
replicaCount: 3

image:
  repository: metamcp/server
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: metamcp.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: metamcp-tls
      hosts:
        - metamcp.yourdomain.com

config:
  secretKey: "your-secret-key"
  jwtSecretKey: "your-jwt-secret"
  openaiApiKey: "your-openai-key"

postgresql:
  enabled: true
  auth:
    username: metamcp
    password: secure-password
    database: metamcp

weaviate:
  enabled: true
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"

redis:
  enabled: true
  auth:
    enabled: false
```

## 🌐 Production Deployment

### Load Balancer Configuration

#### Nginx

```nginx
upstream metamcp_backend {
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 80;
    server_name metamcp.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name metamcp.yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    location / {
        proxy_pass http://metamcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /mcp/ws {
        proxy_pass http://metamcp_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### HAProxy

```haproxy
global
    daemon
    log stdout local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend metamcp_frontend
    bind *:80
    bind *:443 ssl crt /path/to/ssl/cert.pem
    redirect scheme https if !{ ssl_fc }
    default_backend metamcp_backend

backend metamcp_backend
    balance roundrobin
    option httpchk GET /health
    server metamcp1 10.0.1.10:8000 check
    server metamcp2 10.0.1.11:8000 check
    server metamcp3 10.0.1.12:8000 check
```

### Database Setup

#### PostgreSQL Production Configuration

```sql
-- Create production database
CREATE DATABASE metamcp;
CREATE USER metamcp WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE metamcp TO metamcp;

-- Enable extensions
\c metamcp
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

#### Connection Pooling with PgBouncer

```ini
[databases]
metamcp = host=postgres port=5432 dbname=metamcp

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = session
max_client_conn = 100
default_pool_size = 25
```

### Weaviate Production Setup

```yaml
# docker-compose.weaviate.yml
version: '3.8'
services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    ports:
      - "8088:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: 'your-api-key'
      AUTHENTICATION_APIKEY_USERS: 'admin'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: 'text2vec-openai,backup-filesystem'
      BACKUP_FILESYSTEM_PATH: '/backups'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
      - weaviate_backups:/backups
    restart: unless-stopped
```

## 📊 Monitoring & Observability

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'metamcp'
    static_configs:
      - targets: ['metamcp:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'weaviate'
    static_configs:
      - targets: ['weaviate:8080']
    metrics_path: '/v1/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Grafana Dashboards

Import the provided Grafana dashboards:

```bash
# Import dashboards
curl -X POST \
  http://admin:admin@grafana:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana/dashboards/metamcp-overview.json
```

### Logging

#### Centralized Logging with ELK Stack

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  paths:
    - /app/logs/*.log
  fields:
    service: metamcp
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "metamcp-%{+yyyy.MM.dd}"
```

#### Log Aggregation with Fluentd

```conf
<source>
  @type tail
  path /app/logs/metamcp.log
  pos_file /var/log/fluentd/metamcp.log.pos
  tag metamcp.app
  format json
</source>

<match metamcp.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name metamcp
  type_name _doc
</match>
```

## 🔒 Security Considerations

### SSL/TLS Configuration

```bash
# Generate SSL certificate with Let's Encrypt
certbot --nginx -d metamcp.yourdomain.com
```

### Network Security

```bash
# Firewall rules (UFW)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 8000/tcp  # Block direct access to app
ufw enable
```

### Container Security

```dockerfile
# Use non-root user
FROM python:3.11-slim
RUN groupadd -r metamcp && useradd -r -g metamcp metamcp
USER metamcp

# Security scanning
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
```

## 🚨 Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup-db.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
mkdir -p $BACKUP_DIR

pg_dump -h postgres -U metamcp metamcp | gzip > \
  $BACKUP_DIR/metamcp_backup_$TIMESTAMP.sql.gz

# Retention policy (keep 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### Weaviate Backup

```bash
#!/bin/bash
# backup-weaviate.sh
curl -X POST \
  http://weaviate:8080/v1/backups/filesystem \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "backup-'$(date +%Y%m%d_%H%M%S)'",
    "include": ["ToolRegistry", "ToolEmbeddings"]
  }'
```

### Disaster Recovery

1. **Automated Backups**: Set up automated daily backups
2. **Cross-Region Replication**: Replicate data to different regions
3. **Recovery Testing**: Regularly test recovery procedures
4. **Documentation**: Maintain up-to-date recovery procedures

## 📈 Scaling

### Horizontal Scaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: metamcp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: metamcp
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Scaling

#### Read Replicas

```yaml
postgresql:
  readReplicas:
    enabled: true
    replicaCount: 2
    persistence:
      size: 100Gi
```

#### Connection Pooling

```python
# Database connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
```

## 🔍 Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose logs metamcp-server

# Check health
curl http://localhost:8000/health

# Check dependencies
docker-compose ps
```

#### Database Connection Issues

```bash
# Test database connection
psql -h localhost -p 5432 -U metamcp -d metamcp

# Check database logs
docker-compose logs postgres
```

#### Weaviate Issues

```bash
# Check Weaviate health
curl http://localhost:8088/v1/meta

# Check Weaviate logs
docker-compose logs weaviate
```

### Performance Tuning

#### Application Tuning

```python
# FastAPI performance settings
workers = min(4, (os.cpu_count() or 1) + 1)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
```

#### Database Tuning

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/your-org/MetaMCP/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/MetaMCP/issues)
- **Community**: [Discord](https://discord.gg/metamcp)
- **Email**: support@metamcp.org