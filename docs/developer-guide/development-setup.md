# Development Setup

This guide will help you set up a development environment for MetaMCP.

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for dependencies

### Required Software

1. **Python 3.11+**
   ```bash
   # Check Python version
   python --version
   
   # Install Python 3.11 if needed
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```

2. **uv Package Manager**
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/bin/env
   
   # Verify installation
   uv --version
   ```

3. **Git**
   ```bash
   # Install Git
   sudo apt install git
   
   # Configure Git
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

4. **Docker** (optional, for local services)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo apt install docker-compose-plugin
   ```

## Development Environment Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/lichtbaer/MetaMCP.git
cd MetaMCP

# Check out development branch
git checkout develop
```

### 2. Create Virtual Environment

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate

# Verify activation
which python
# Should show: /path/to/MetaMCP/.venv/bin/python
```

### 3. Install Dependencies

```bash
# Install development dependencies
uv pip install -r requirements.txt

# Install additional development tools
uv pip install -r requirements-dev.txt
```

### 4. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit environment file
nano .env
```

Configure your `.env` file for development:

```env
# Development settings
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
TELEMETRY_ENABLED=false

# OpenAI (required for embeddings)
OPENAI_API_KEY=sk-your-openai-api-key

# Security (development only)
SECRET_KEY=dev-secret-key-change-in-production

# Database (SQLite for development)
DATABASE_URL=sqlite:///./metamcp.db

# Vector database (optional)
WEAVIATE_URL=http://localhost:8080

# OPA (optional)
OPA_URL=http://localhost:8181

# Development tools
DOCS_ENABLED=true
ADMIN_ENABLED=true
```

### 5. Initialize Database

```bash
# Run database migrations
python -m metamcp.utils.db migrate

# Create initial data
python -m metamcp.utils.db seed
```

### 6. Start Local Services (Optional)

For full development experience, start local services with Docker:

```bash
# Start local services
docker-compose up -d postgres weaviate redis opa

# Check services
docker-compose ps
```

## Development Tools Setup

### 1. Pre-commit Hooks

```bash
# Install pre-commit
uv pip install pre-commit

# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### 2. Code Quality Tools

```bash
# Install linting tools
uv pip install ruff bandit mypy

# Configure tools
ruff check --fix .
bandit -r metamcp/
mypy metamcp/
```

### 3. Testing Setup

```bash
# Install testing tools
uv pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=metamcp tests/
```

### 4. Documentation Tools

```bash
# Install documentation tools
uv pip install mkdocs mkdocs-material

# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

## IDE Setup

### VS Code

1. **Install VS Code Extensions**:
   ```bash
   code --install-extension ms-python.python
   code --install-extension ms-python.black-formatter
   code --install-extension ms-python.flake8
   code --install-extension ms-python.mypy-type-checker
   code --install-extension charliermarsh.ruff
   ```

2. **VS Code Settings** (`.vscode/settings.json`):
   ```json
   {
     "python.defaultInterpreterPath": "./.venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.ruffEnabled": true,
     "python.formatting.provider": "black",
     "python.testing.pytestEnabled": true,
     "python.testing.pytestArgs": ["tests"],
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

### PyCharm

1. **Configure Python Interpreter**:
   - Go to Settings → Project → Python Interpreter
   - Add interpreter from `.venv/bin/python`

2. **Configure Code Style**:
   - Settings → Editor → Code Style → Python
   - Set line length to 88 (Black default)

3. **Configure Testing**:
   - Settings → Tools → Python Integrated Tools
   - Set default test runner to pytest

## Development Workflow

### 1. Starting Development Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start development server
python -m metamcp.main

# Or with auto-reload
uvicorn metamcp.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=metamcp --cov-report=html

# Run integration tests
pytest tests/integration/

# Run unit tests only
pytest tests/unit/
```

### 3. Code Quality Checks

```bash
# Run all quality checks
make quality

# Or run individually
ruff check .
ruff format .
bandit -r metamcp/
mypy metamcp/
```

### 4. Documentation

```bash
# Build documentation
mkdocs build

# Serve documentation
mkdocs serve

# Deploy documentation
mkdocs gh-deploy
```

## Database Development

### 1. Database Migrations

```bash
# Create new migration
python -m metamcp.utils.db migrate --message "Add user table"

# Apply migrations
python -m metamcp.utils.db upgrade

# Rollback migration
python -m metamcp.utils.db downgrade
```

### 2. Database Seeding

```bash
# Seed development data
python -m metamcp.utils.db seed

# Seed specific data
python -m metamcp.utils.db seed --fixture users
```

### 3. Database Reset

```bash
# Reset database (development only)
python -m metamcp.utils.db reset

# Reset and seed
python -m metamcp.utils.db reset --seed
```

## API Development

### 1. API Testing

```bash
# Start server
python -m metamcp.main

# Test API endpoints
curl http://localhost:8000/health

# Test with authentication
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/tools
```

### 2. API Documentation

```bash
# Access Swagger UI
open http://localhost:8000/docs

# Access ReDoc
open http://localhost:8000/redoc
```

### 3. API Testing with Postman

1. **Import Collection**: Import `postman/MetaMCP.postman_collection.json`
2. **Set Environment Variables**:
   - `base_url`: `http://localhost:8000`
   - `token`: Your JWT token

## Debugging

### 1. Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start server with debug
python -m metamcp.main
```

### 2. Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Use logger
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### 3. Debugging with VS Code

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: MetaMCP",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/metamcp/main.py",
      "console": "integratedTerminal",
      "env": {
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

## Performance Development

### 1. Profiling

```bash
# Install profiling tools
uv pip install cProfile-to-html snakeviz

# Profile code
python -m cProfile -o profile.stats metamcp/main.py

# View profile results
snakeviz profile.stats
```

### 2. Memory Profiling

```bash
# Install memory profiler
uv pip install memory-profiler

# Profile memory usage
python -m memory_profiler metamcp/main.py
```

### 3. Load Testing

```bash
# Install load testing tools
uv pip install locust

# Run load test
locust -f tests/load/locustfile.py
```

## Contributing Guidelines

### 1. Code Style

- Follow PEP 8 with Black formatting
- Use type hints for all functions
- Write docstrings for all public functions
- Keep functions small and focused

### 2. Testing

- Write unit tests for all new code
- Maintain 80%+ code coverage
- Write integration tests for API endpoints
- Test error conditions and edge cases

### 3. Documentation

- Update documentation for new features
- Add examples for new API endpoints
- Update configuration reference
- Add troubleshooting guides

### 4. Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... edit files ...

# Run quality checks
make quality

# Run tests
pytest

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push branch
git push origin feature/new-feature

# Create pull request
# ... create PR on GitHub ...
```

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Reinstall dependencies
   uv pip install -r requirements.txt
   ```

2. **Database Connection**:
   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Test connection
   python -c "from metamcp.utils.db import test_connection; test_connection()"
   ```

3. **OpenAI API Issues**:
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   
   # Test API connection
   python -c "from metamcp.llm import test_openai; test_openai()"
   ```

4. **Port Conflicts**:
   ```bash
   # Check port usage
   lsof -i :8000
   
   # Kill process using port
   kill -9 <PID>
   ```

### Getting Help

- **Documentation**: Check the [docs](../index.md)
- **Issues**: [GitHub Issues](https://github.com/lichtbaer/MetaMCP/issues)
- **Discord**: [Community Support](https://discord.gg/metamcp)
- **Email**: [Developer Support](mailto:dev@example.com) 