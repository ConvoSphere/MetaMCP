#!/bin/bash

# Vault Kubernetes Deployment Script
# This script automates the deployment of HashiCorp Vault with External Secrets Operator

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VAULT_NAMESPACE="vault"
EXTERNAL_SECRETS_NAMESPACE="external-secrets"
METAMCP_NAMESPACE="metamcp"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if kubectl is configured
    if ! kubectl cluster-info &> /dev/null; then
        log_error "kubectl is not configured. Please configure kubectl first."
        exit 1
    fi
    
    # Check if jq is installed (for JSON parsing)
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. Installing jq..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            sudo yum install -y jq
        elif command -v brew &> /dev/null; then
            brew install jq
        else
            log_error "Cannot install jq automatically. Please install jq manually."
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

deploy_vault() {
    log_info "Deploying Vault..."
    
    # Create namespaces
    kubectl apply -f namespace.yaml
    
    # Apply Vault resources
    kubectl apply -f configmap.yaml
    kubectl apply -f pvc.yaml
    kubectl apply -f rbac.yaml
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
    
    # Wait for Vault to be ready
    log_info "Waiting for Vault to be ready..."
    kubectl wait --for=condition=ready pod -l app=vault,component=server -n $VAULT_NAMESPACE --timeout=300s
    
    log_success "Vault deployed successfully"
}

initialize_vault() {
    log_info "Initializing Vault..."
    
    # Apply initialization job
    kubectl apply -f vault-init.yaml
    
    # Wait for initialization job to complete
    log_info "Waiting for Vault initialization to complete..."
    kubectl wait --for=condition=complete job/vault-init -n $VAULT_NAMESPACE --timeout=600s
    
    # Check if initialization was successful
    if kubectl get job vault-init -n $VAULT_NAMESPACE -o jsonpath='{.status.succeeded}' | grep -q "1"; then
        log_success "Vault initialized successfully"
    else
        log_error "Vault initialization failed"
        kubectl logs job/vault-init -n $VAULT_NAMESPACE
        exit 1
    fi
}

deploy_external_secrets() {
    log_info "Deploying External Secrets Operator..."
    
    # Apply External Secrets Operator
    kubectl apply -f external-secrets.yaml
    
    # Wait for External Secrets Operator to be ready
    log_info "Waiting for External Secrets Operator to be ready..."
    kubectl wait --for=condition=ready pod -l app=external-secrets,component=operator -n $EXTERNAL_SECRETS_NAMESPACE --timeout=300s
    
    log_success "External Secrets Operator deployed successfully"
}

configure_secret_store() {
    log_info "Configuring Secret Store..."
    
    # Apply Secret Store configuration
    kubectl apply -f secret-store.yaml
    
    # Wait for External Secret to be ready
    log_info "Waiting for External Secret to be ready..."
    kubectl wait --for=condition=ready externalsecret/metamcp-secrets -n $METAMCP_NAMESPACE --timeout=300s
    
    log_success "Secret Store configured successfully"
}

deploy_ingress() {
    log_info "Deploying Vault Ingress..."
    
    # Create basic auth secret for Vault UI
    kubectl create secret generic vault-basic-auth \
      --from-literal=auth=admin:\$2y\$10\$rQZ9X7Y8Z9X7Y8Z9X7Y8Z9X7Y8Z9X7Y8Z9X7Y8Z9X7Y8Z9X7Y8Z9X7Y8 \
      --dry-run=client -o yaml | kubectl apply -f - -n $VAULT_NAMESPACE
    
    # Apply Ingress
    kubectl apply -f ingress.yaml
    
    log_success "Vault Ingress deployed successfully"
}

setup_vault_secrets() {
    log_info "Setting up Vault secrets for MetaMCP..."
    
    # Port forward to Vault
    kubectl port-forward svc/vault 8200:8200 -n $VAULT_NAMESPACE &
    PF_PID=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Set Vault address
    export VAULT_ADDR="http://localhost:8200"
    export VAULT_SKIP_VERIFY="true"
    
    # Get root token from initialization job
    ROOT_TOKEN=$(kubectl logs job/vault-init -n $VAULT_NAMESPACE | grep "Root Token:" | awk '{print $3}')
    
    if [ -z "$ROOT_TOKEN" ]; then
        log_error "Could not retrieve root token from Vault initialization"
        kill $PF_PID 2>/dev/null || true
        exit 1
    fi
    
    # Login to Vault
    echo $ROOT_TOKEN | vault login -
    
    # Update secrets with real values (if provided)
    if [ ! -z "${OPENAI_API_KEY:-}" ]; then
        vault kv put secret/metamcp/llm openai_api_key="$OPENAI_API_KEY"
        log_info "Updated OpenAI API key"
    fi
    
    if [ ! -z "${GOOGLE_OAUTH_CLIENT_ID:-}" ]; then
        vault kv put secret/metamcp/oauth google_client_id="$GOOGLE_OAUTH_CLIENT_ID"
        log_info "Updated Google OAuth client ID"
    fi
    
    if [ ! -z "${GOOGLE_OAUTH_CLIENT_SECRET:-}" ]; then
        vault kv put secret/metamcp/oauth google_client_secret="$GOOGLE_OAUTH_CLIENT_SECRET"
        log_info "Updated Google OAuth client secret"
    fi
    
    # Kill port forward
    kill $PF_PID 2>/dev/null || true
    
    log_success "Vault secrets configured successfully"
}

show_status() {
    log_info "Vault deployment status:"
    
    echo
    echo "=== Vault Pods ==="
    kubectl get pods -n $VAULT_NAMESPACE
    
    echo
    echo "=== Vault Services ==="
    kubectl get svc -n $VAULT_NAMESPACE
    
    echo
    echo "=== External Secrets Operator ==="
    kubectl get pods -n $EXTERNAL_SECRETS_NAMESPACE
    
    echo
    echo "=== External Secrets ==="
    kubectl get externalsecrets -n $METAMCP_NAMESPACE
    
    echo
    echo "=== Secret Stores ==="
    kubectl get secretstores -n $METAMCP_NAMESPACE
}

show_access_info() {
    log_info "Vault access information:"
    
    echo
    echo "=== Vault UI ==="
    echo "URL: https://vault.metamcp.example.com"
    echo "Username: admin"
    echo "Password: (check vault-basic-auth secret)"
    
    echo
    echo "=== Vault API ==="
    echo "Internal: http://vault.vault.svc.cluster.local:8200"
    echo "External: https://vault.metamcp.example.com"
    
    echo
    echo "=== Port Forward (for local access) ==="
    echo "kubectl port-forward svc/vault 8200:8200 -n $VAULT_NAMESPACE"
    
    echo
    echo "=== Vault CLI ==="
    echo "export VAULT_ADDR=http://localhost:8200"
    echo "export VAULT_SKIP_VERIFY=true"
    echo "vault login"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Kill any background processes
    jobs -p | xargs -r kill
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting Vault deployment..."
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    check_prerequisites
    deploy_vault
    initialize_vault
    deploy_external_secrets
    configure_secret_store
    deploy_ingress
    setup_vault_secrets
    show_status
    show_access_info
    
    log_success "Vault deployment completed successfully!"
}

# Uninstall function
uninstall() {
    log_warning "This will delete all Vault resources from the cluster!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Uninstalling Vault..."
        
        # Delete resources in reverse order
        kubectl delete -f secret-store.yaml --ignore-not-found
        kubectl delete -f external-secrets.yaml --ignore-not-found
        kubectl delete -f vault-init.yaml --ignore-not-found
        kubectl delete -f ingress.yaml --ignore-not-found
        kubectl delete -f service.yaml --ignore-not-found
        kubectl delete -f deployment.yaml --ignore-not-found
        kubectl delete -f rbac.yaml --ignore-not-found
        kubectl delete -f pvc.yaml --ignore-not-found
        kubectl delete -f configmap.yaml --ignore-not-found
        kubectl delete namespace $VAULT_NAMESPACE --ignore-not-found
        kubectl delete namespace $EXTERNAL_SECRETS_NAMESPACE --ignore-not-found
        
        log_success "Vault uninstalled successfully"
    else
        log_info "Uninstall cancelled"
    fi
}

# Status function
status() {
    show_status
    show_access_info
}

# Usage function
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy     Deploy Vault with External Secrets Operator (default)"
    echo "  uninstall  Uninstall all Vault resources"
    echo "  status     Show deployment status"
    echo "  help       Show this help message"
    echo
    echo "Environment Variables:"
    echo "  OPENAI_API_KEY              OpenAI API key to store in Vault"
    echo "  GOOGLE_OAUTH_CLIENT_ID      Google OAuth client ID"
    echo "  GOOGLE_OAUTH_CLIENT_SECRET  Google OAuth client secret"
    echo
    echo "Examples:"
    echo "  $0 deploy"
    echo "  OPENAI_API_KEY=sk-... $0 deploy"
    echo "  $0 uninstall"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    uninstall)
        uninstall
        ;;
    status)
        status
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac