#!/bin/bash

# Start MetaMCP Monitoring Stack
# This script starts the complete monitoring stack including Prometheus, Grafana, Jaeger, and AlertManager

set -e

echo "🚀 Starting MetaMCP Monitoring Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create monitoring directory structure
echo "📁 Creating monitoring directory structure..."
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards

# Create Grafana datasource configuration
cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Create Grafana dashboard configuration
cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# Create basic MetaMCP dashboard
cat > monitoring/grafana/dashboards/metamcp-overview.json << EOF
{
  "dashboard": {
    "id": null,
    "title": "MetaMCP Overview",
    "tags": ["metamcp"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamcp_requests_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, metamcp_request_duration_seconds)",
            "legendFormat": "95th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Tool Executions",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamcp_tool_executions_total[5m])",
            "legendFormat": "{{tool_name}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Vector Searches",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(metamcp_vector_searches_total[5m])",
            "legendFormat": "searches/sec"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "10s"
  }
}
EOF

# Start monitoring stack
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "🔍 Checking service status..."
docker-compose -f docker-compose.monitoring.yml ps

# Display access URLs
echo ""
echo "✅ Monitoring stack is ready!"
echo ""
echo "📊 Access URLs:"
echo "   Grafana:     http://localhost:3000 (admin/admin)"
echo "   Prometheus:  http://localhost:9090"
echo "   Jaeger:      http://localhost:16686"
echo "   AlertManager: http://localhost:9093"
echo ""
echo "🔧 Configuration:"
echo "   - Prometheus config: monitoring/prometheus.yml"
echo "   - Alert rules: monitoring/alert_rules.yml"
echo "   - AlertManager config: monitoring/alertmanager.yml"
echo "   - OTEL Collector config: monitoring/otel-collector-config.yml"
echo ""
echo "📈 Next steps:"
echo "   1. Open Grafana and add Prometheus as data source"
echo "   2. Import the MetaMCP dashboard"
echo "   3. Configure alerts in AlertManager"
echo "   4. Start your MetaMCP application with telemetry enabled"
echo ""
echo "🛑 To stop the monitoring stack:"
echo "   docker-compose -f docker-compose.monitoring.yml down" 