#!/bin/bash

# =============================================================================
# MCP Meta-Server Development Startup Script
# =============================================================================
#
# This script sets up and starts the MCP Meta-Server in development mode
# with all required services and dependencies.

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
        log_error "Python 3.8 or higher is required. Current version: $python_version"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

setup_environment() {
    log_info "Setting up environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create .env file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        log_warning "Please edit .env file with your configuration before continuing"
        log_warning "Especially set SECRET_KEY, JWT_SECRET_KEY, and ADMIN_UI_SECRET_KEY"
    fi
    
    # Create necessary directories
    mkdir -p logs data policies/compiled
    
    # Set permissions
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "Environment setup complete"
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    log_success "Python environment setup complete"
}

start_infrastructure() {
    log_info "Starting infrastructure services..."
    
    cd "$PROJECT_ROOT"
    
    # Start core infrastructure services
    docker-compose up -d postgres weaviate redis opa
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    until docker-compose exec postgres pg_isready -U metamcp > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""
    log_success "PostgreSQL is ready"
    
    # Wait for Weaviate
    until curl -s http://localhost:9088/v1/meta > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""
    log_success "Weaviate is ready"
    
    # Wait for Redis
    until docker-compose exec redis redis-cli ping > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""
    log_success "Redis is ready"
    
    # Wait for OPA
    until curl -s http://localhost:8181/health > /dev/null 2>&1; do
        echo -n "."
        sleep 1
    done
    echo ""
    log_success "OPA is ready"
    
    log_success "All infrastructure services are running"
}

setup_database() {
    log_info "Setting up database..."
    
    cd "$PROJECT_ROOT"
    
    # Run database migrations (when implemented)
    # source venv/bin/activate
    # alembic upgrade head
    
    log_success "Database setup complete"
}

compile_policies() {
    log_info "Compiling OPA policies..."
    
    cd "$PROJECT_ROOT"
    
    # Compile policies (optional optimization)
    if command -v opa &> /dev/null; then
        opa fmt --diff policies/*.rego
        # opa build policies/ -o policies/compiled/bundle.tar.gz
    else
        log_warning "OPA CLI not installed, skipping policy compilation"
    fi
    
    log_success "Policies compiled"
}

start_server() {
    log_info "Starting MCP Meta-Server..."
    
    cd "$PROJECT_ROOT"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set development environment variables
    export DEBUG=true
    export LOG_LEVEL=DEBUG
    export AUTO_RELOAD=true
    
    # Start the server
    python -m metamcp.main
}

show_status() {
    log_info "Development Environment Status:"
    echo ""
    echo "Services:"
    echo "  • MCP Meta-Server: http://localhost:9000"
echo "  • API Documentation: http://localhost:9000/docs"
    echo "  • Admin API: http://localhost:9000/api/v1/admin"
    echo "  • Weaviate: http://localhost:9088"
    echo "  • PostgreSQL: localhost:5432"
    echo "  • Redis: localhost:6380"
    echo "  • OPA: http://localhost:8181"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    echo "Logs:"
    echo "  • Application logs: ./logs/metamcp.log"
    echo "  • Docker logs: docker-compose logs -f"
    echo ""
}

cleanup() {
    log_info "Cleaning up..."
    docker-compose down
    log_success "Cleanup complete"
}

# Main script
main() {
    log_info "Starting MCP Meta-Server Development Environment"
    echo ""
    
    # Parse command line arguments
    case "${1:-}" in
        "stop")
            cleanup
            exit 0
            ;;
        "status")
            show_status
            exit 0
            ;;
        "clean")
            cleanup
            log_info "Removing volumes..."
            docker-compose down -v
            docker volume prune -f
            log_success "Clean complete"
            exit 0
            ;;
        "--help"|"-h")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start (default) - Start the development environment"
            echo "  stop           - Stop all services"
            echo "  status         - Show service status and URLs"
            echo "  clean          - Stop services and remove volumes"
            echo "  --help, -h     - Show this help"
            exit 0
            ;;
    esac
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Setup development environment
    check_dependencies
    setup_environment
    setup_python_environment
    start_infrastructure
    setup_database
    compile_policies
    
    show_status
    
    log_success "Development environment is ready!"
    log_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the server (this will block)
    start_server
}

# Handle interrupts
trap cleanup INT TERM

# Run main function
main "$@"