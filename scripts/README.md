# MetaMCP CLI Tool

A comprehensive command-line interface for managing the MetaMCP project. This tool bundles all script functionalities in a modular way.

## Quick Start

```bash
# Make the CLI executable
chmod +x metamcp-cli

# Run the CLI
./metamcp-cli --help
```

## Available Commands

### Environment Management

```bash
# Validate environment configuration
./metamcp-cli validate

# Set up development environment
./metamcp-cli dev setup

# Install dependencies
./metamcp-cli dev install
```

### Development

```bash
# Start development environment
./metamcp-cli dev start

# Start monitoring stack
./metamcp-cli dev monitoring
```

### Docker Management

```bash
# Show container status
./metamcp-cli docker status

# Show logs for all containers
./metamcp-cli docker logs

# Show logs for specific service
./metamcp-cli docker logs metamcp-server

# Restart all containers
./metamcp-cli docker restart

# Restart specific service
./metamcp-cli docker restart metamcp-server

# Stop all containers
./metamcp-cli docker stop

# Build all containers
./metamcp-cli docker build

# Build specific service
./metamcp-cli docker build metamcp-server

# Build without cache
./metamcp-cli docker build --no-cache
```

### Testing

```bash
# Run all tests
./metamcp-cli test all

# Run unit tests
./metamcp-cli test unit

# Run integration tests
./metamcp-cli test integration

# Run blackbox tests
./metamcp-cli test blackbox
```

### Code Quality

```bash
# Run code linting
./metamcp-cli quality lint

# Format code
./metamcp-cli quality format

# Run security checks
./metamcp-cli quality security
```

### Documentation

```bash
# Build documentation
./metamcp-cli docs build

# Serve documentation locally
./metamcp-cli docs serve
```

### Project Information

```bash
# Show project information
./metamcp-cli info
```

## Scripts Directory Structure

```
scripts/
├── cli.py              # Main CLI tool
├── validate_env.py      # Environment validation
├── docker_utils.py      # Docker utilities
├── test_utils.py        # Test utilities
├── docs_utils.py        # Documentation utilities
├── start-dev.sh         # Development startup script
├── start-monitoring.sh  # Monitoring startup script
└── README.md           # This file
```

## Modular Design

The CLI tool is built with a modular design:

### Core CLI (`cli.py`)
- Main command-line interface
- Argument parsing and routing
- High-level command execution

### Environment Validation (`validate_env.py`)
- Environment variable validation
- Configuration checks
- Dependency verification

### Docker Utilities (`docker_utils.py`)
- Container management
- Service health checks
- Resource monitoring
- Cleanup operations

### Test Utilities (`test_utils.py`)
- Test execution
- Coverage reporting
- Quality checks
- Dependency verification

### Documentation Utilities (`docs_utils.py`)
- Documentation building
- Local serving
- Structure validation
- API documentation generation

## Shell Scripts

### Development Startup (`start-dev.sh`)
- Sets up development environment
- Starts infrastructure services
- Compiles policies
- Launches development server

### Monitoring Startup (`start-monitoring.sh`)
- Starts monitoring stack
- Configures Grafana dashboards
- Sets up Prometheus
- Configures AlertManager

## Usage Examples

### Complete Development Setup

```bash
# 1. Set up environment
./metamcp-cli dev setup

# 2. Install dependencies
./metamcp-cli dev install

# 3. Validate configuration
./metamcp-cli validate

# 4. Start development environment
./metamcp-cli dev start

# 5. Check status
./metamcp-cli docker status
```

### Testing Workflow

```bash
# 1. Run all tests
./metamcp-cli test all

# 2. Check code quality
./metamcp-cli quality lint
./metamcp-cli quality format
./metamcp-cli quality security

# 3. Generate test report
./metamcp-cli test all
```

### Documentation Workflow

```bash
# 1. Validate documentation
./metamcp-cli docs build

# 2. Serve locally for review
./metamcp-cli docs serve

# 3. Deploy to GitHub Pages (if configured)
./metamcp-cli docs deploy
```

### Troubleshooting

```bash
# Check project status
./metamcp-cli info

# View container logs
./metamcp-cli docker logs metamcp-server

# Restart problematic service
./metamcp-cli docker restart metamcp-server

# Rebuild containers
./metamcp-cli docker build --no-cache
```

## Configuration

The CLI tool uses the same configuration as the main application:

- Environment variables (see `env.example`)
- Docker Compose configuration
- Project structure

## Dependencies

The CLI tool requires:

- Python 3.8+
- Docker and Docker Compose
- Project dependencies (see `requirements.txt`)

## Contributing

When adding new functionality:

1. Create a new utility module in `scripts/`
2. Add corresponding commands to `cli.py`
3. Update this README with new commands
4. Add tests if applicable

## Error Handling

The CLI tool provides:

- Clear error messages
- Exit codes for automation
- Graceful failure handling
- Dependency checking

## Integration

The CLI tool integrates with:

- Docker Compose for container management
- pytest for testing
- mkdocs for documentation
- Various code quality tools 