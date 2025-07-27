# Development Guide

Entwickler-Guide für MetaMCP.

## 🚀 Setup

```bash
# Repository klonen
git clone https://github.com/metamcp/metamcp.git
cd metamcp

# Virtual Environment
python -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Development install
pip install -e .
```

## 🧪 Tests

```bash
# Alle Tests
pytest

# Unit Tests
pytest tests/unit/

# Integration Tests
pytest tests/integration/

# Blackbox Tests
pytest tests/blackbox/

# Mit Coverage
pytest --cov=metamcp tests/
```

## 🔍 Code Quality

```bash
# Linting
flake8 metamcp/
ruff check metamcp/

# Type Checking
mypy metamcp/

# Security
bandit -r metamcp/

# Formatting
black metamcp/
isort metamcp/
```

## 🏗️ Architektur

### Module-Struktur
```
metamcp/
├── api/           # REST API Endpoints
├── services/      # Business Logic
├── composition/   # Workflow Engine
├── admin/         # Admin Interface
├── security/      # Auth & Policies
├── monitoring/    # Health & Metrics
├── utils/         # Utilities
└── config.py      # Configuration
```

### Services
- `AuthService`: Benutzer-Management
- `ToolService`: Tool-Registry
- `SearchService`: Tool-Suche
- `CompositionService`: Workflow-Engine

## 📝 Coding Standards

### Python
```python
# Type Hints verwenden
def create_user(user_data: Dict[str, Any]) -> str:
    """Create a new user."""
    pass

# Docstrings
def get_tool(tool_id: str) -> Optional[Tool]:
    """
    Get tool by ID.
    
    Args:
        tool_id: Tool identifier
        
    Returns:
        Tool object or None if not found
    """
    pass
```

### API Endpoints
```python
@router.post("/tools")
async def create_tool(
    tool_data: ToolCreateRequest,
    current_user: User = Depends(get_current_user)
) -> ToolResponse:
    """Create a new tool."""
    pass
```

## 🔧 Development Workflow

### 1. Feature Branch
```bash
git checkout -b feature/your-feature
```

### 2. Entwicklung
```bash
# Hot Reload
uvicorn metamcp.main:app --reload

# Tests laufen lassen
pytest tests/unit/your-module/
```

### 3. Commit
```bash
git add .
git commit -m "feat: add new tool endpoint"
```

### 4. Pull Request
```bash
git push origin feature/your-feature
# PR erstellen
```

## 🧪 Testing

### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch

class TestToolService:
    def test_create_tool(self):
        """Test tool creation."""
        service = ToolService()
        result = service.create_tool({"name": "test"})
        assert result is not None
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_tool_workflow():
    """Test complete tool workflow."""
    # Setup
    # Execute
    # Assert
```

### API Tests
```python
async def test_create_tool_api(client):
    """Test tool creation API."""
    response = await client.post("/api/v1/tools", json=tool_data)
    assert response.status_code == 201
```

## 🔍 Debugging

### Logging
```python
from metamcp.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing tool", extra={"tool_id": tool_id})
```

### Debug Mode
```bash
DEBUG=true python -m metamcp.main
```

### Database
```bash
# SQLite Browser
sqlite3 metamcp.db

# PostgreSQL
psql -h localhost -U metamcp -d metamcp
```

## 📊 Monitoring

### Health Checks
```bash
curl http://localhost:8000/api/v1/health
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

### Logs
```bash
tail -f logs/metamcp.log
```

## 🚀 Deployment

### Docker Build
```bash
docker build -t metamcp .
docker run -p 8000:8000 metamcp
```

### Docker Compose
```bash
docker-compose up -d
```

### Production
```bash
# Environment
export ENVIRONMENT=production
export DEBUG=false

# Start
gunicorn metamcp.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📚 Ressourcen

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://pydantic-docs.helpmanual.io/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pytest Docs](https://docs.pytest.org/)