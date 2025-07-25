#!/usr/bin/env python3
"""
Integration tests for the MetaMCP CLI tool.

This module tests the CLI functionality with real file operations
and command execution in a controlled environment.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
from scripts.cli import MetaMCPCLI

sys.path.insert(0, str(project_root))


class TestCLIIntegration:
    """Integration tests for the CLI tool."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for integration testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create project structure
            (temp_path / "scripts").mkdir()
            (temp_path / "metamcp").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "docs").mkdir()
            (temp_path / "policies").mkdir()
            (temp_path / "monitoring").mkdir()

            # Create basic files
            (temp_path / "docker-compose.yml").write_text(
                "version: '3.8'\nservices:\n  test:\n    image: test"
            )
            (temp_path / "requirements.txt").write_text("pytest\nrequests")
            (temp_path / "pyproject.toml").write_text(
                "[tool.pytest]\ntestpaths = ['tests']"
            )
            (temp_path / "mkdocs.yml").write_text("site_name: Test Docs")

            # Create .env file
            env_content = """APP_NAME=TestApp
DEBUG=true
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
SECRET_KEY=test-secret-key
DATABASE_URL=postgresql://test:test@localhost/test
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
OPA_URL=http://localhost:8181
OPENAI_API_KEY=test-key
VECTOR_SEARCH_ENABLED=true
TELEMETRY_ENABLED=true
OTLP_ENDPOINT=
ADMIN_ENABLED=true
ADMIN_PORT=8501
"""
            (temp_path / ".env").write_text(env_content)

            # Create env.example
            example_content = """APP_NAME=MetaMCP
DEBUG=false
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=postgresql://user:password@localhost/metamcp
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
OPA_URL=http://localhost:8181
OPENAI_API_KEY=your-openai-api-key
VECTOR_SEARCH_ENABLED=true
TELEMETRY_ENABLED=true
OTLP_ENDPOINT=
ADMIN_ENABLED=true
ADMIN_PORT=8501
"""
            (temp_path / "env.example").write_text(example_content)

            yield temp_path

    def test_cli_initialization_integration(self, temp_project):
        """Test CLI initialization with real project structure."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test that CLI can find project files
            assert cli.project_root.exists()
            assert (cli.project_root / "docker-compose.yml").exists()
            assert (cli.project_root / "requirements.txt").exists()
            assert (cli.project_root / ".env").exists()
            assert (cli.project_root / "env.example").exists()

        finally:
            os.chdir(original_cwd)

    def test_environment_validation_integration(self, temp_project):
        """Test environment validation with real .env file."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test environment validation
            result = cli.validate_environment()

            # Should be valid with our test environment
            assert result["valid"] is True
            assert len(result["errors"]) == 0
            assert "APP_NAME" in result["environment_info"]
            assert result["environment_info"]["APP_NAME"] == "TestApp"

        finally:
            os.chdir(original_cwd)

    def test_env_show_integration(self, temp_project):
        """Test env show command with real files."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test env show
            with patch("builtins.print") as mock_print:
                cli.env_show()
                mock_print.assert_called()

                # Verify that env content was printed
                calls = mock_print.call_args_list
                env_content_found = False
                for call in calls:
                    if "APP_NAME=TestApp" in str(call):
                        env_content_found = True
                        break
                assert env_content_found

        finally:
            os.chdir(original_cwd)

    def test_env_diff_integration(self, temp_project):
        """Test env diff command with real files."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test env diff
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "1,2c1,2\n< APP_NAME=TestApp\n< DEBUG=true\n---\n> APP_NAME=MetaMCP\n> DEBUG=false"
                mock_run.return_value.stderr = ""

                with patch("builtins.print") as mock_print:
                    cli.env_diff()
                    mock_print.assert_called()

                    # Verify that diff was printed
                    calls = mock_print.call_args_list
                    diff_content_found = False
                    for call in calls:
                        if "APP_NAME=TestApp" in str(call) or "APP_NAME=MetaMCP" in str(
                            call
                        ):
                            diff_content_found = True
                            break
                    assert diff_content_found

        finally:
            os.chdir(original_cwd)

    def test_env_edit_integration(self, temp_project):
        """Test env edit command with real files."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test env edit
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0

                cli.env_edit()
                mock_run.assert_called_once()

                # Verify that editor was called with .env file
                call_args = mock_run.call_args[0][0]
                assert ".env" in call_args

        finally:
            os.chdir(original_cwd)

    def test_docker_status_integration(self, temp_project):
        """Test docker status command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test docker status
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = (
                    '{"Name": "test-container", "Status": "running"}'
                )
                mock_run.return_value.stderr = ""

                with patch("builtins.print") as mock_print:
                    cli.docker_status()
                    mock_print.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_docker_logs_integration(self, temp_project):
        """Test docker logs command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test docker logs
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "Container logs here"
                mock_run.return_value.stderr = ""

                with patch("builtins.print") as mock_print:
                    cli.docker_logs("test-service")
                    mock_print.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_dev_setup_integration(self, temp_project):
        """Test dev setup command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test dev setup
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                result = cli.setup_environment()
                assert result == 0
                mock_run.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_dev_install_integration(self, temp_project):
        """Test dev install command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test dev install
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                result = cli.install_dependencies()
                assert result == 0
                mock_run.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_test_unit_integration(self, temp_project):
        """Test test unit command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test test unit
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                result = cli.run_tests("unit")
                assert result == 0
                mock_run.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_quality_lint_integration(self, temp_project):
        """Test quality lint command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test quality lint
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                result = cli.lint_code()
                assert result == 0
                mock_run.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_docs_build_integration(self, temp_project):
        """Test docs build command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test docs build
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                result = cli.generate_docs()
                assert result == 0
                mock_run.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_update_integration(self, temp_project):
        """Test update command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test update
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                with patch("builtins.print") as mock_print:
                    cli.update_project()
                    mock_print.assert_called()
                    # Should call multiple update commands
                    assert mock_run.call_count >= 2

        finally:
            os.chdir(original_cwd)

    def test_reset_integration(self, temp_project):
        """Test reset command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test reset
            with patch.object(cli, "run_command") as mock_run:
                mock_run.return_value = 0

                with patch("builtins.input", return_value="yes"):
                    with patch("builtins.print") as mock_print:
                        cli.reset_project(hard=False)
                        mock_print.assert_called()
                        # Should call reset commands
                        assert mock_run.call_count >= 1

        finally:
            os.chdir(original_cwd)

    def test_info_integration(self, temp_project):
        """Test info command."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            cli = MetaMCPCLI()

            # Test info
            with patch("builtins.print") as mock_print:
                cli.show_project_info()
                mock_print.assert_called()

                # Verify that project info was printed
                calls = mock_print.call_args_list
                info_found = False
                for call in calls:
                    if "MetaMCP" in str(call) or "TestApp" in str(call):
                        info_found = True
                        break
                assert info_found

        finally:
            os.chdir(original_cwd)


class TestCLIErrorHandling:
    """Test CLI error handling in integration scenarios."""

    @pytest.fixture
    def temp_project_with_errors(self):
        """Create a temporary project with potential error conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create minimal structure
            (temp_path / "scripts").mkdir()

            # Create invalid docker-compose file
            (temp_path / "docker-compose.yml").write_text("invalid yaml: content")

            # Create invalid requirements file
            (temp_path / "requirements.txt").write_text("invalid-package-name")

            yield temp_path

    def test_cli_with_invalid_docker_compose(self, temp_project_with_errors):
        """Test CLI behavior with invalid docker-compose.yml."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project_with_errors)

        try:
            cli = MetaMCPCLI()

            # Test docker status with invalid compose file
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "Invalid docker-compose.yml"

                with patch("builtins.print") as mock_print:
                    cli.docker_status()
                    mock_print.assert_called()

        finally:
            os.chdir(original_cwd)

    def test_cli_with_missing_files(self, temp_project_with_errors):
        """Test CLI behavior with missing project files."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project_with_errors)

        try:
            cli = MetaMCPCLI()

            # Test environment validation with missing .env
            result = cli.validate_environment()

            # Should detect missing .env file
            assert result["valid"] is False
            assert len(result["missing_required"]) > 0

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
