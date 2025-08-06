# HashiCorp Vault with External Secrets Operator

This directory contains Kubernetes manifests for deploying HashiCorp Vault with External Secrets Operator for secure secrets management in the MetaMCP environment.

## 📁 File Structure

```
k8s/vault/
├── namespace.yaml              # Namespace definitions
├── configmap.yaml              # Vault configuration
├── deployment.yaml             # Vault server deployment
├── service.yaml                # Vault services
├── pvc.yaml                    # Persistent volume claims
├── rbac.yaml                   # RBAC configuration
├── external-secrets.yaml       # External Secrets Operator
├── secret-store.yaml           # Secret store configuration
├── vault-init.yaml             # Vault initialization job
├── ingress.yaml                # Vault UI ingress
├── kustomization.yaml          # Kustomize configuration
├── deploy.sh                   # Deployment script
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes Cluster** (v1.24+)
2. **kubectl** configured
3. **jq** installed (for JSON parsing)
4. **NGINX Ingress Controller** installed
5. **cert-manager** installed (for TLS)

### 1. Deploy Vault

```bash
cd k8s/vault
./deploy.sh deploy
```

### 2. Deploy with Secrets

```bash
# Deploy with API keys
OPENAI_API_KEY="sk-your-openai-key" \
GOOGLE_OAUTH_CLIENT_ID="your-google-client-id" \
GOOGLE_OAUTH_CLIENT_SECRET="your-google-client-secret" \
./deploy.sh deploy
```

### 3. Verify Deployment

```bash
./deploy.sh status
```

## 🔧 Configuration

### Vault Configuration

Key configuration options in `configmap.yaml`:

- **Storage Backend**: File storage (demo) / Consul/etcd (production)
- **Authentication**: Kubernetes auth enabled
- **Audit Logging**: File-based audit logging
- **Telemetry**: Prometheus metrics enabled

### Production Configuration

For production environments, update the Vault configuration:

```hcl
# Enable HA mode with Consul
ha_storage "consul" {
  address = "consul:8500"
  path    = "vault/"
  service = "vault"
}

# Enable auto-unseal with AWS KMS
seal "awskms" {
  region     = "us-west-2"
  kms_key_id = "alias/vault-unseal"
}

# Enable TLS
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 0
  tls_cert_file = "/vault/tls/tls.crt"
  tls_key_file = "/vault/tls/tls.key"
}
```

## 🔐 Secrets Management

### Secret Structure

Vault organizes secrets in the following structure:

```
secret/metamcp/
├── database/
│   └── url                    # Database connection string
├── auth/
│   └── secret_key            # JWT secret key
├── llm/
│   ├── openai_api_key        # OpenAI API key
│   └── openai_base_url       # OpenAI base URL
├── vector/
│   └── weaviate_api_key      # Weaviate API key
├── oauth/
│   ├── google_client_id      # Google OAuth client ID
│   ├── google_client_secret  # Google OAuth client secret
│   ├── github_client_id      # GitHub OAuth client ID
│   ├── github_client_secret  # GitHub OAuth client secret
│   ├── microsoft_client_id   # Microsoft OAuth client ID
│   └── microsoft_client_secret # Microsoft OAuth client secret
└── cache/
    ├── redis_url             # Redis cache URL
    └── rate_limit_redis_url  # Rate limiting Redis URL
```

### Adding New Secrets

```bash
# Port forward to Vault
kubectl port-forward svc/vault 8200:8200 -n vault

# Set Vault environment
export VAULT_ADDR="http://localhost:8200"
export VAULT_SKIP_VERIFY="true"

# Login (get token from initialization logs)
vault login

# Add new secret
vault kv put secret/metamcp/new-service api_key="your-api-key"
```

### Updating External Secrets

After adding secrets to Vault, update the External Secret:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: metamcp-secrets
spec:
  data:
  - secretKey: NEW_API_KEY
    remoteRef:
      key: metamcp/new-service
      property: api_key
```

## 🔒 Security Features

### Authentication

- **Kubernetes Auth**: Service accounts authenticate with Vault
- **Token-based**: Short-lived tokens for API access
- **Policy-based**: Fine-grained access control

### Policies

MetaMCP application policy allows:

- Read access to application secrets
- List access to secret metadata
- Update access to own service account secrets

### Network Security

- **Network Policies**: Restrict pod-to-pod communication
- **TLS**: Encrypted communication (production)
- **Ingress Security**: Basic auth and rate limiting

## 📊 Monitoring

### Health Checks

- **Liveness Probe**: `/v1/sys/health`
- **Readiness Probe**: `/v1/sys/health`
- **Metrics**: `/v1/sys/metrics`

### Metrics

Vault exposes Prometheus metrics:

```bash
# Get metrics
curl http://vault:8200/v1/sys/metrics
```

### Logging

- **Audit Logs**: All secret access logged
- **Application Logs**: Structured JSON logging
- **Centralized**: Integrated with cluster logging

## 🔄 Operations

### Backup and Restore

```bash
# Backup Vault data
kubectl exec -it deployment/vault -n vault -- vault operator raft snapshot save /tmp/backup.snap

# Restore Vault data
kubectl exec -it deployment/vault -n vault -- vault operator raft snapshot restore /tmp/backup.snap
```

### Scaling

```bash
# Scale Vault (for HA mode)
kubectl scale deployment vault --replicas=3 -n vault
```

### Updates

```bash
# Update Vault version
kubectl set image deployment/vault vault=vault:1.16.0 -n vault

# Check rollout status
kubectl rollout status deployment/vault -n vault
```

## 🚨 Troubleshooting

### Common Issues

1. **Vault Not Initialized**
   ```bash
   kubectl logs job/vault-init -n vault
   ```

2. **External Secrets Not Syncing**
   ```bash
   kubectl describe externalsecret metamcp-secrets -n metamcp
   kubectl logs deployment/external-secrets -n external-secrets
   ```

3. **Authentication Issues**
   ```bash
   kubectl describe secretstore vault-backend -n metamcp
   ```

### Debug Commands

```bash
# Check Vault status
kubectl exec -it deployment/vault -n vault -- vault status

# Check External Secrets status
kubectl get externalsecrets -n metamcp
kubectl describe externalsecret metamcp-secrets -n metamcp

# Check Secret Store status
kubectl get secretstores -n metamcp
kubectl describe secretstore vault-backend -n metamcp

# Check generated secrets
kubectl get secret metamcp-secrets -n metamcp -o yaml
```

## 🌐 Access

### Vault UI

- **URL**: https://vault.metamcp.example.com
- **Username**: admin
- **Password**: (check vault-basic-auth secret)

### Vault API

- **Internal**: http://vault.vault.svc.cluster.local:8200
- **External**: https://vault.metamcp.example.com

### Port Forward

```bash
# Local access
kubectl port-forward svc/vault 8200:8200 -n vault

# Set environment
export VAULT_ADDR="http://localhost:8200"
export VAULT_SKIP_VERIFY="true"
```

## 📋 Checklist

- [ ] Vault deployed and initialized
- [ ] External Secrets Operator deployed
- [ ] Secret Store configured
- [ ] External Secret created
- [ ] Secrets synced to Kubernetes
- [ ] MetaMCP application using Vault secrets
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Security policies reviewed
- [ ] Documentation updated

## 🔗 Integration with MetaMCP

### Environment Variables

MetaMCP automatically uses secrets from Vault through External Secrets Operator:

```yaml
envFrom:
- secretRef:
    name: metamcp-secrets  # Created by External Secrets Operator
```

### Secret Rotation

To rotate secrets:

1. Update secret in Vault
2. External Secrets Operator automatically syncs
3. Restart MetaMCP pods to pick up new secrets

```bash
# Update secret in Vault
vault kv put secret/metamcp/auth secret_key="new-secret-key"

# Restart MetaMCP
kubectl rollout restart deployment/metamcp-deployment -n metamcp
```

## 🆘 Support

For issues and questions:

1. Check Vault logs: `kubectl logs deployment/vault -n vault`
2. Check External Secrets logs: `kubectl logs deployment/external-secrets -n external-secrets`
3. Check External Secret status: `kubectl describe externalsecret metamcp-secrets -n metamcp`
4. Review this documentation
5. Check Vault documentation: https://www.vaultproject.io/docs
6. Check External Secrets documentation: https://external-secrets.io