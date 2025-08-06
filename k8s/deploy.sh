#!/bin/bash

# MetaMCP Kubernetes Deployment Script
# This script automates the deployment of MetaMCP to Kubernetes

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="metamcp"
DEPLOYMENT_NAME="metamcp-deployment"
ADMIN_DEPLOYMENT_NAME="metamcp-admin-deployment"
SERVICE_NAME="metamcp-service"
ADMIN_SERVICE_NAME="metamcp-admin-service"

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
    
    # Check if kustomize is installed (optional)
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize is not installed. Will use kubectl apply -k instead."
    fi
    
    log_success "Prerequisites check passed"
}

validate_manifests() {
    log_info "Validating Kubernetes manifests..."
    
    # Validate with kustomize if available
    if command -v kustomize &> /dev/null; then
        if ! kustomize build . | kubectl apply --dry-run=client -f -; then
            log_error "Manifest validation failed"
            exit 1
        fi
    else
        # Validate individual files
        for file in *.yaml; do
            if [[ "$file" != "kustomization.yaml" ]]; then
                if ! kubectl apply --dry-run=client -f "$file"; then
                    log_error "Validation failed for $file"
                    exit 1
                fi
            fi
        done
    fi
    
    log_success "Manifest validation passed"
}

create_namespace() {
    log_info "Creating namespace..."
    kubectl apply -f namespace.yaml
    log_success "Namespace created"
}

apply_resources() {
    log_info "Applying Kubernetes resources..."
    
    # Apply resources in order
    kubectl apply -f configmap.yaml
    kubectl apply -f secret.yaml
    kubectl apply -f rbac.yaml
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
    kubectl apply -f network-policy.yaml
    kubectl apply -f ingress.yaml
    kubectl apply -f hpa.yaml
    kubectl apply -f pdb.yaml
    
    log_success "Resources applied successfully"
}

wait_for_deployment() {
    log_info "Waiting for deployments to be ready..."
    
    # Wait for main deployment
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s
    
    # Wait for admin deployment
    kubectl rollout status deployment/$ADMIN_DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s
    
    log_success "Deployments are ready"
}

check_health() {
    log_info "Checking application health..."
    
    # Wait a bit for services to be ready
    sleep 10
    
    # Check if services are accessible
    if kubectl get svc $SERVICE_NAME -n $NAMESPACE &> /dev/null; then
        log_success "Main service is accessible"
    else
        log_error "Main service is not accessible"
        return 1
    fi
    
    if kubectl get svc $ADMIN_SERVICE_NAME -n $NAMESPACE &> /dev/null; then
        log_success "Admin service is accessible"
    else
        log_error "Admin service is not accessible"
        return 1
    fi
    
    # Check health endpoints
    log_info "Checking health endpoints..."
    
    # Port forward to check health
    kubectl port-forward svc/$SERVICE_NAME 8080:80 -n $NAMESPACE &
    PF_PID=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Check health endpoint
    if curl -f http://localhost:8080/health &> /dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        kill $PF_PID 2>/dev/null || true
        return 1
    fi
    
    # Kill port forward
    kill $PF_PID 2>/dev/null || true
    
    log_success "All health checks passed"
}

show_status() {
    log_info "Deployment status:"
    
    echo
    echo "=== Pods ==="
    kubectl get pods -n $NAMESPACE
    
    echo
    echo "=== Services ==="
    kubectl get svc -n $NAMESPACE
    
    echo
    echo "=== Deployments ==="
    kubectl get deployments -n $NAMESPACE
    
    echo
    echo "=== Ingress ==="
    kubectl get ingress -n $NAMESPACE
    
    echo
    echo "=== HPA ==="
    kubectl get hpa -n $NAMESPACE
    
    echo
    echo "=== PDB ==="
    kubectl get pdb -n $NAMESPACE
}

show_access_info() {
    log_info "Access information:"
    
    echo
    echo "=== External Access ==="
    echo "API: https://metamcp.example.com"
    echo "Admin: https://admin.metamcp.example.com"
    echo "Docs: https://metamcp.example.com/docs"
    echo "Health: https://metamcp.example.com/health"
    echo "Metrics: https://metamcp.example.com/metrics"
    
    echo
    echo "=== Internal Access ==="
    echo "API Service: $SERVICE_NAME.$NAMESPACE.svc.cluster.local"
    echo "Admin Service: $ADMIN_SERVICE_NAME.$NAMESPACE.svc.cluster.local"
    
    echo
    echo "=== Port Forward (for local testing) ==="
    echo "kubectl port-forward svc/$SERVICE_NAME 8080:80 -n $NAMESPACE"
    echo "kubectl port-forward svc/$ADMIN_SERVICE_NAME 9501:80 -n $NAMESPACE"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Kill any background processes
    jobs -p | xargs -r kill
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting MetaMCP deployment..."
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    check_prerequisites
    validate_manifests
    create_namespace
    apply_resources
    wait_for_deployment
    check_health
    show_status
    show_access_info
    
    log_success "MetaMCP deployment completed successfully!"
}

# Rollback function
rollback() {
    log_info "Rolling back deployment..."
    
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    kubectl rollout undo deployment/$ADMIN_DEPLOYMENT_NAME -n $NAMESPACE
    
    wait_for_deployment
    show_status
    
    log_success "Rollback completed"
}

# Delete function
delete() {
    log_warning "This will delete all MetaMCP resources from the cluster!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting MetaMCP resources..."
        
        kubectl delete namespace $NAMESPACE
        
        log_success "MetaMCP resources deleted"
    else
        log_info "Deletion cancelled"
    fi
}

# Usage function
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy    Deploy MetaMCP to Kubernetes (default)"
    echo "  rollback  Rollback to previous deployment"
    echo "  delete    Delete all MetaMCP resources"
    echo "  status    Show deployment status"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 rollback"
    echo "  $0 delete"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    delete)
        delete
        ;;
    status)
        show_status
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