# MetaMCP Kubernetes Deployment

This directory contains all Kubernetes manifests for deploying MetaMCP as a production-ready microservice.

## 📁 File Structure

```
k8s/
├── namespace.yaml          # Namespace definitions
├── configmap.yaml          # Non-sensitive configuration
├── secret.yaml            # Sensitive configuration (API keys, passwords)
├── rbac.yaml              # RBAC (ServiceAccount, Role, RoleBinding)
├── deployment.yaml        # Application deployments
├── service.yaml           # Service definitions
├── network-policy.yaml    # Network security policies
├── ingress.yaml           # External access configuration
├── hpa.yaml              # Horizontal Pod Autoscaler
├── pdb.yaml              # Pod Disruption Budgets
├── kustomization.yaml    # Kustomize configuration
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes Cluster** (v1.24+)
2. **kubectl** configured
3. **Docker image** built and pushed to registry
4. **NGINX Ingress Controller** installed
5. **cert-manager** installed (for TLS)

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t metamcp/metamcp:latest .

# Push to registry (replace with your registry)
docker push metamcp/metamcp:latest
```

### 2. Update Secrets

**⚠️ IMPORTANT**: Update the secrets in `secret.yaml` with your actual values:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update secrets
kubectl create secret generic metamcp-secrets \
  --from-literal=OPENAI_API_KEY=your_openai_api_key \
  --from-literal=SECRET_KEY=your_generated_secret_key \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Deploy to Kubernetes

```bash
# Apply all resources
kubectl apply -k .

# Or apply individually
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f rbac.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f network-policy.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
kubectl apply -f pdb.yaml
```

### 4. Verify Deployment

```bash
# Check all resources
kubectl get all -n metamcp

# Check pods
kubectl get pods -n metamcp

# Check services
kubectl get svc -n metamcp

# Check ingress
kubectl get ingress -n metamcp

# Check logs
kubectl logs -f deployment/metamcp-deployment -n metamcp
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `configmap.yaml`:

- `ENVIRONMENT`: production/staging/development
- `DEBUG`: true/false
- `WORKERS`: Number of worker processes
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR
- `CORS_ORIGINS`: Allowed origins for CORS

### Resource Limits

Default resource configuration:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Scaling Configuration

HPA settings:

- **Min Replicas**: 2
- **Max Replicas**: 10
- **CPU Target**: 70%
- **Memory Target**: 80%

## 🔒 Security Features

### Network Policies

- Restricts pod-to-pod communication
- Allows only necessary traffic
- Blocks unauthorized access

### RBAC

- ServiceAccount with minimal permissions
- Role-based access control
- Principle of least privilege

### Security Context

- Non-root user execution
- Read-only root filesystem
- Dropped capabilities
- Seccomp profile enabled

## 📊 Monitoring

### Health Checks

- **Liveness Probe**: `/health/live`
- **Readiness Probe**: `/health/ready`
- **Startup Probe**: `/health`

### Metrics

- Prometheus metrics endpoint: `/metrics`
- Custom application metrics
- Resource utilization metrics

### Logging

- Structured JSON logging
- Configurable log levels
- Centralized log collection

## 🔄 Updates and Rollouts

### Rolling Updates

```bash
# Update image
kubectl set image deployment/metamcp-deployment metamcp-api=metamcp/metamcp:v1.1.0 -n metamcp

# Check rollout status
kubectl rollout status deployment/metamcp-deployment -n metamcp

# Rollback if needed
kubectl rollout undo deployment/metamcp-deployment -n metamcp
```

### Blue-Green Deployment

```bash
# Create new deployment
kubectl apply -f deployment-v2.yaml

# Switch traffic
kubectl patch service metamcp-service -p '{"spec":{"selector":{"version":"v1.1.0"}}}'
```

## 🚨 Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   ```bash
   kubectl describe pod <pod-name> -n metamcp
   kubectl logs <pod-name> -n metamcp
   ```

2. **Service Not Accessible**
   ```bash
   kubectl get endpoints -n metamcp
   kubectl describe service metamcp-service -n metamcp
   ```

3. **Ingress Issues**
   ```bash
   kubectl describe ingress metamcp-ingress -n metamcp
   kubectl get events -n metamcp
   ```

### Debug Commands

```bash
# Port forward for local access
kubectl port-forward svc/metamcp-service 8080:80 -n metamcp

# Exec into pod
kubectl exec -it <pod-name> -n metamcp -- /bin/bash

# Check resource usage
kubectl top pods -n metamcp
```

## 📈 Scaling

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment metamcp-deployment --replicas=5 -n metamcp
```

### Auto Scaling

HPA automatically scales based on:
- CPU utilization
- Memory utilization
- Custom metrics

## 🔐 Secrets Management

### External Secrets (Recommended)

For production, use external secret management:

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets

# Create ExternalSecret
kubectl apply -f external-secret.yaml
```

### Manual Secret Updates

```bash
# Update specific secret
kubectl patch secret metamcp-secrets -p '{"data":{"OPENAI_API_KEY":"'$(echo -n "new_key" | base64)'"}}' -n metamcp

# Restart pods to pick up new secrets
kubectl rollout restart deployment/metamcp-deployment -n metamcp
```

## 🌐 DNS Configuration

Update your DNS to point to the ingress controller:

```bash
# Get ingress controller IP
kubectl get svc -n ingress-nginx

# Add DNS records
# metamcp.example.com -> <ingress-ip>
# admin.metamcp.example.com -> <ingress-ip>
```

## 📋 Checklist

- [ ] Docker image built and pushed
- [ ] Secrets updated with real values
- [ ] DNS configured
- [ ] Ingress controller installed
- [ ] cert-manager installed
- [ ] All resources deployed
- [ ] Health checks passing
- [ ] TLS certificate issued
- [ ] Monitoring configured
- [ ] Backup strategy in place

## 🆘 Support

For issues and questions:

1. Check the logs: `kubectl logs -f deployment/metamcp-deployment -n metamcp`
2. Check events: `kubectl get events -n metamcp`
3. Check resource status: `kubectl get all -n metamcp`
4. Review this documentation
5. Check the main project README