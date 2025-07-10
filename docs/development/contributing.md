# Contributing to MetaMCP

Thank you for your interest in contributing to MetaMCP! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11+
- uv package manager
- Git
- Docker (for testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/your-username/MetaMCP.git
cd MetaMCP
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/original-owner/MetaMCP.git
```

## Development Setup

### Environment Setup

1. Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

### Configuration

1. Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

2. Update the configuration with your development settings:

```yaml
# Development configuration
app:
  name: "MetaMCP"
  version: "1.0.0"
  debug: true

server:
  host: "0.0.0.0"
  port: 8000

database:
  url: "sqlite:///./metamcp_dev.db"

vector_search:
  provider: "weaviate"
  url: "http://localhost:8080"
  api_key: "your-weaviate-key"

llm:
  provider: "openai"
  api_key: "your-openai-key"
  model: "gpt-4"

telemetry:
  enabled: true
  otlp_endpoint: "http://localhost:4317"
  prometheus_port: 9090
```

### Running the Application

1. Start the development server:

```bash
python -m metamcp.main
```

2. Or use the development script:

```bash
./scripts/start-dev.sh
```

3. Access the application:

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all function parameters and return values
- Use docstrings for all public functions and classes
- Prefer f-strings over `.format()` or `%` formatting

### Code Formatting

We use several tools for code formatting:

```bash
# Format code with Black
black metamcp/ tests/

# Sort imports with isort
isort metamcp/ tests/

# Check code style with flake8
flake8 metamcp/ tests/

# Type checking with mypy
mypy metamcp/
```

### Pre-commit Hooks

The project includes pre-commit hooks that automatically format and check your code:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Naming Conventions

- **Files**: Use snake_case for Python files
- **Classes**: Use PascalCase
- **Functions and Variables**: Use snake_case
- **Constants**: Use UPPER_SNAKE_CASE
- **Private Methods**: Prefix with underscore

### Documentation Standards

- Use Google-style docstrings
- Include type hints
- Document all public APIs
- Provide examples for complex functions

Example docstring:

```python
def calculate_sum(a: float, b: float) -> float:
    """Calculate the sum of two numbers.
    
    Args:
        a: First number to add
        b: Second number to add
        
    Returns:
        The sum of a and b
        
    Raises:
        ValueError: If either input is not a number
        
    Example:
        >>> calculate_sum(5.0, 3.0)
        8.0
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Inputs must be numbers")
    return a + b
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=metamcp --cov-report=html

# Run specific test file
pytest tests/test_tools.py

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Test Structure

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Performance Tests**: Test performance and scalability
- **Security Tests**: Test security measures
- **End-to-End Tests**: Test complete workflows

### Writing Tests

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Test Structure**: Follow the Arrange-Act-Assert pattern
3. **Test Isolation**: Each test should be independent
4. **Mocking**: Use mocks for external dependencies
5. **Fixtures**: Use pytest fixtures for common setup

Example test:

```python
import pytest
from unittest.mock import Mock, patch
from metamcp.tools.registry import ToolRegistry

class TestToolRegistry:
    """Test tool registry functionality."""
    
    @pytest.fixture
    def tool_registry(self):
        """Create tool registry for testing."""
        return ToolRegistry()
    
    @pytest.mark.asyncio
    async def test_register_tool(self, tool_registry):
        """Test tool registration."""
        # Arrange
        tool_data = {
            "name": "Calculator",
            "description": "Perform calculations",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"}
        }
        
        # Act
        tool_id = await tool_registry.register_tool(tool_data)
        
        # Assert
        assert tool_id is not None
        assert await tool_registry.get_tool(tool_id) is not None
```

### Test Coverage

We aim for at least 90% test coverage. To check coverage:

```bash
pytest --cov=metamcp --cov-report=term-missing
```

## Documentation

### Documentation Standards

- Write clear, concise documentation
- Use proper Markdown formatting
- Include code examples
- Keep documentation up to date with code changes

### Building Documentation

```bash
# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

### Documentation Structure

- **User Guide**: Installation, configuration, usage
- **API Reference**: Complete API documentation
- **Developer Guide**: Contributing, development setup
- **Architecture**: System design and components
- **Deployment**: Production deployment guide

## Pull Request Process

### Before Submitting

1. **Create a Feature Branch**:

```bash
git checkout -b feature/your-feature-name
```

2. **Make Your Changes**:
   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation
   - Update changelog if needed

3. **Test Your Changes**:

```bash
# Run all tests
pytest

# Run linting
black --check metamcp/ tests/
isort --check-only metamcp/ tests/
flake8 metamcp/ tests/
mypy metamcp/

# Run security checks
bandit -r metamcp/
safety check -r requirements.txt
```

4. **Commit Your Changes**:

```bash
git add .
git commit -m "feat: add new feature description

- Detailed description of changes
- Any breaking changes
- Related issues"
```

### Commit Message Format

We use Conventional Commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

### Submitting a Pull Request

1. **Push Your Branch**:

```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request**:
   - Use the PR template
   - Provide clear description
   - Link related issues
   - Add screenshots if UI changes

3. **PR Checklist**:
   - [ ] Code follows style guidelines
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] Security considerations addressed

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: At least one maintainer must approve
3. **Address Feedback**: Respond to review comments
4. **Merge**: Once approved, maintainers will merge

## Release Process

### Versioning

We use Semantic Versioning (SemVer):

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Steps

1. **Update Version**:
   - Update version in `metamcp/__init__.py`
   - Update version in `pyproject.toml`

2. **Update Changelog**:
   - Add release notes to `CHANGELOG.md`
   - Include all changes since last release

3. **Create Release Branch**:

```bash
git checkout -b release/v1.0.0
git commit -m "chore: release v1.0.0"
git push origin release/v1.0.0
```

4. **Create GitHub Release**:
   - Tag the release
   - Add release notes
   - Upload artifacts

5. **Publish to PyPI**:

```bash
# Build package
python -m build

# Upload to PyPI
twine upload dist/*
```

## Community

### Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our Discord server for real-time chat

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time community chat
- **Email**: For security issues

### Recognition

Contributors are recognized in:

- **README.md**: List of contributors
- **CHANGELOG.md**: Credit for contributions
- **GitHub**: Contributor graph and profile

### Mentorship

We offer mentorship for new contributors:

- **Good First Issues**: Labeled for beginners
- **Mentorship Program**: Pair with experienced contributors
- **Documentation**: Comprehensive guides and tutorials

## Security

### Security Policy

- **Responsible Disclosure**: Report security issues privately
- **Security Updates**: Prompt response to security issues
- **Vulnerability Management**: Regular security audits

### Reporting Security Issues

For security issues, please email security@metamcp.org instead of creating a public issue.

## License

By contributing to MetaMCP, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please:

1. Check the documentation
2. Search existing issues and discussions
3. Ask in GitHub Discussions
4. Join our Discord server

Thank you for contributing to MetaMCP! 