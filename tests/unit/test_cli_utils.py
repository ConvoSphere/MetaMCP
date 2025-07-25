#!/usr/bin/env python3
"""
Unit tests for CLI utility modules.

This module tests the utility functions used by the CLI tool.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
from scripts.docker_utils import DockerUtils
from scripts.docs_utils import DocsUtils
from scripts.test_utils import TestUtils
from scripts.validate_env import (
    print_validation_results,
    suggest_fixes,
    validate_environment,
)

sys.path.insert(0, str(project_root))


class TestDockerUtils:
    """Test the DockerUtils class."""

    @pytest.fixture
    def docker_utils(self):
        """Create a DockerUtils instance for testing."""
        project_root = Path("/tmp/test_project")
        return DockerUtils(project_root)

    def test_docker_utils_initialization(self, docker_utils):
        """Test DockerUtils initialization."""
        assert docker_utils.project_root == Path("/tmp/test_project")

    def test_check_docker_available(self, docker_utils):
        """Test Docker availability check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            assert docker_utils.check_docker_available() is True

            mock_run.return_value.returncode = 1
            assert docker_utils.check_docker_available() is False

    def test_check_docker_compose_available(self, docker_utils):
        """Test Docker Compose availability check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            assert docker_utils.check_docker_compose_available() is True

            mock_run.return_value.returncode = 1
            assert docker_utils.check_docker_compose_available() is False

    def test_get_container_status(self, docker_utils):
        """Test container status retrieval."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = (
                '{"Name": "test-container", "Status": "running"}'
            )

            result = docker_utils.get_container_status()
            assert result["running"] is True
            assert len(result["containers"]) > 0

    def test_get_container_logs(self, docker_utils):
        """Test container logs retrieval."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Container logs here"

            result = docker_utils.get_container_logs("test-service")
            assert "Container logs here" in result

    def test_build_containers(self, docker_utils):
        """Test container building."""
        with patch.object(docker_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docker_utils.build_containers("test-service", no_cache=True)
            assert result == 0
            mock_run.assert_called_once()

    def test_start_containers(self, docker_utils):
        """Test container starting."""
        with patch.object(docker_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docker_utils.start_containers("test-service")
            assert result == 0
            mock_run.assert_called_once()

    def test_stop_containers(self, docker_utils):
        """Test container stopping."""
        with patch.object(docker_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docker_utils.stop_containers("test-service")
            assert result == 0
            mock_run.assert_called_once()

    def test_restart_containers(self, docker_utils):
        """Test container restarting."""
        with patch.object(docker_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docker_utils.restart_containers("test-service")
            assert result == 0
            mock_run.assert_called_once()

    def test_pull_images(self, docker_utils):
        """Test image pulling."""
        with patch.object(docker_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docker_utils.pull_images()
            assert result == 0
            mock_run.assert_called_once()

    def test_clean_containers(self, docker_utils):
        """Test container cleanup."""
        with patch.object(docker_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docker_utils.clean_containers()
            assert result == 0
            # Should call multiple cleanup commands
            assert mock_run.call_count >= 4

    def test_check_services_health(self, docker_utils):
        """Test service health checking."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = docker_utils.check_services_health()
            assert isinstance(result, dict)
            # Should check multiple services
            assert len(result) > 0


class TestTestUtils:
    """Test the TestUtils class."""

    @pytest.fixture
    def test_utils(self):
        """Create a TestUtils instance for testing."""
        project_root = Path("/tmp/test_project")
        return TestUtils(project_root)

    def test_test_utils_initialization(self, test_utils):
        """Test TestUtils initialization."""
        assert test_utils.project_root == Path("/tmp/test_project")

    def test_check_test_dependencies(self, test_utils):
        """Test test dependency checking."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = test_utils.check_test_dependencies()
            assert isinstance(result, dict)
            # Should check multiple dependencies
            assert len(result) > 0

    def test_run_unit_tests(self, test_utils):
        """Test unit test execution."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_unit_tests()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_integration_tests(self, test_utils):
        """Test integration test execution."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_integration_tests()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_blackbox_tests(self, test_utils):
        """Test blackbox test execution."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_blackbox_tests()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_performance_tests(self, test_utils):
        """Test performance test execution."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_performance_tests()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_security_tests(self, test_utils):
        """Test security test execution."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_security_tests()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_all_tests(self, test_utils):
        """Test all tests execution."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_all_tests()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_linting(self, test_utils):
        """Test code linting."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_linting()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_formatting(self, test_utils):
        """Test code formatting."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_formatting()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_security_checks(self, test_utils):
        """Test security checks."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_security_checks()
            assert result == 0
            mock_run.assert_called_once()

    def test_run_type_checking(self, test_utils):
        """Test type checking."""
        with patch.object(test_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = test_utils.run_type_checking()
            assert result == 0
            mock_run.assert_called_once()

    def test_generate_test_report(self, test_utils):
        """Test test report generation."""
        with patch.object(test_utils, "run_all_tests") as mock_run:
            mock_run.return_value = 0

            result = test_utils.generate_test_report()
            assert result == 0
            mock_run.assert_called_once()

    def test_check_test_coverage(self, test_utils):
        """Test test coverage checking."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "TOTAL 100 0 100%"

            result = test_utils.check_test_coverage(80.0)
            assert result is True


class TestDocsUtils:
    """Test the DocsUtils class."""

    @pytest.fixture
    def docs_utils(self):
        """Create a DocsUtils instance for testing."""
        project_root = Path("/tmp/test_project")
        return DocsUtils(project_root)

    def test_docs_utils_initialization(self, docs_utils):
        """Test DocsUtils initialization."""
        assert docs_utils.project_root == Path("/tmp/test_project")
        assert docs_utils.docs_dir == Path("/tmp/test_project/docs")

    def test_check_docs_dependencies(self, docs_utils):
        """Test documentation dependency checking."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = docs_utils.check_docs_dependencies()
            assert isinstance(result, dict)
            # Should check multiple dependencies
            assert len(result) > 0

    def test_build_docs(self, docs_utils):
        """Test documentation building."""
        with patch.object(docs_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docs_utils.build_docs()
            assert result == 0
            mock_run.assert_called_once()

    def test_serve_docs(self, docs_utils):
        """Test documentation serving."""
        with patch.object(docs_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docs_utils.serve_docs()
            assert result == 0
            mock_run.assert_called_once()

    def test_deploy_docs(self, docs_utils):
        """Test documentation deployment."""
        with patch.object(docs_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docs_utils.deploy_docs()
            assert result == 0
            mock_run.assert_called_once()

    def test_validate_docs(self, docs_utils):
        """Test documentation validation."""
        with patch.object(docs_utils, "build_docs") as mock_build:
            mock_build.return_value = 0

            result = docs_utils.validate_docs()
            assert result == 0
            mock_build.assert_called_once()

    def test_generate_api_docs(self, docs_utils):
        """Test API documentation generation."""
        with patch.object(docs_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docs_utils.generate_api_docs()
            assert result == 0
            mock_run.assert_called()

    def test_update_docs_index(self, docs_utils):
        """Test documentation index update."""
        with patch.object(docs_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docs_utils.update_docs_index()
            assert result == 0

    def test_create_docs_structure(self, docs_utils):
        """Test documentation structure creation."""
        with patch.object(docs_utils, "run_command") as mock_run:
            mock_run.return_value = 0

            result = docs_utils.create_docs_structure()
            assert result == 0


class TestValidateEnv:
    """Test the validate_env module."""

    def test_validate_environment_success(self):
        """Test successful environment validation."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "APP_NAME": "MetaMCP",
                "DEBUG": "false",
                "ENVIRONMENT": "development",
                "HOST": "0.0.0.0",
                "PORT": "8000",
                "LOG_LEVEL": "INFO",
                "SECRET_KEY": "test-key",
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "WEAVIATE_URL": "http://localhost:8080",
                "REDIS_URL": "redis://localhost:6379",
                "OPA_URL": "http://localhost:8181",
                "OPENAI_API_KEY": "test-key",
                "VECTOR_SEARCH_ENABLED": "true",
                "TELEMETRY_ENABLED": "true",
                "OTLP_ENDPOINT": "",
                "ADMIN_ENABLED": "true",
                "ADMIN_PORT": "8501",
            }.get(key, default)

            result = validate_environment()
            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_environment_missing_required(self):
        """Test environment validation with missing required variables."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "APP_NAME": "MetaMCP",
                "DEBUG": "false",
                "ENVIRONMENT": "development",
                "HOST": "0.0.0.0",
                "PORT": "8000",
                "LOG_LEVEL": "INFO",
                "SECRET_KEY": "test-key",
                # Missing required variables
                "DATABASE_URL": None,
                "WEAVIATE_URL": None,
                "REDIS_URL": None,
                "OPA_URL": None,
                "OPENAI_API_KEY": "test-key",
                "VECTOR_SEARCH_ENABLED": "true",
                "TELEMETRY_ENABLED": "true",
                "OTLP_ENDPOINT": "",
                "ADMIN_ENABLED": "true",
                "ADMIN_PORT": "8501",
            }.get(key, default)

            result = validate_environment()
            assert result["valid"] is False
            assert len(result["missing_required"]) > 0

    def test_validate_environment_production_errors(self):
        """Test environment validation for production with errors."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "APP_NAME": "MetaMCP",
                "DEBUG": "true",  # Should be false in production
                "ENVIRONMENT": "production",
                "HOST": "0.0.0.0",
                "PORT": "8000",
                "LOG_LEVEL": "INFO",
                "SECRET_KEY": "your-secret-key-change-in-production",  # Should be changed
                "DATABASE_URL": "postgresql://test:test@localhost/test",
                "WEAVIATE_URL": "http://localhost:8080",
                "REDIS_URL": "redis://localhost:6379",
                "OPA_URL": "http://localhost:8181",
                "OPENAI_API_KEY": "test-key",
                "VECTOR_SEARCH_ENABLED": "true",
                "TELEMETRY_ENABLED": "true",
                "OTLP_ENDPOINT": "",
                "ADMIN_ENABLED": "true",
                "ADMIN_PORT": "8501",
            }.get(key, default)

            result = validate_environment()
            assert result["valid"] is False
            assert len(result["errors"]) > 0

    def test_print_validation_results(self):
        """Test validation results printing."""
        results = {
            "valid": True,
            "errors": [],
            "warnings": ["Test warning"],
            "missing_required": [],
            "environment_info": {"environment": "development"},
        }

        with patch("builtins.print") as mock_print:
            print_validation_results(results)
            mock_print.assert_called()

    def test_suggest_fixes(self):
        """Test fix suggestions."""
        results = {
            "valid": False,
            "errors": ["Debug mode should be disabled"],
            "missing_required": ["SECRET_KEY"],
        }

        with patch("builtins.print") as mock_print:
            suggest_fixes(results)
            mock_print.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
