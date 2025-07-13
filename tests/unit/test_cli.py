#!/usr/bin/env python3
"""
Unit tests for the MetaMCP CLI tool.

This module tests the CLI functionality including command parsing,
environment management, Docker operations, and utility functions.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.cli import MetaMCPCLI, create_parser, main


class TestMetaMCPCLI:
    """Test the MetaMCPCLI class."""
    
    @pytest.fixture
    def cli(self):
        """Create a CLI instance for testing."""
        return MetaMCPCLI()
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create basic project structure
            (temp_path / "scripts").mkdir()
            (temp_path / "metamcp").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "docs").mkdir()
            (temp_path / "policies").mkdir()
            yield temp_path
    
    def test_cli_initialization(self, cli):
        """Test CLI initialization."""
        assert cli.project_root.exists()
        assert cli.scripts_dir.exists()
        assert cli.scripts_dir.name == "scripts"
    
    def test_run_command_success(self, cli):
        """Test successful command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Success"
            mock_run.return_value.stderr = ""
            
            result = cli.run_command(["echo", "test"])
            
            assert result == 0
            mock_run.assert_called_once()
    
    def test_run_command_failure(self, cli):
        """Test failed command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "Error"
            
            result = cli.run_command(["invalid", "command"])
            
            assert result == 1
    
    def test_run_command_exception(self, cli):
        """Test command execution with exception."""
        with patch('subprocess.run', side_effect=Exception("Test error")):
            result = cli.run_command(["echo", "test"])
            assert result == 1


class TestEnvironmentCommands:
    """Test environment-related commands."""
    
    @pytest.fixture
    def temp_env_files(self, temp_project):
        """Create temporary environment files for testing."""
        env_file = temp_project / ".env"
        env_example = temp_project / "env.example"
        
        env_content = """APP_NAME=TestApp
DEBUG=true
DATABASE_URL=postgresql://test:test@localhost/test
"""
        env_example_content = """APP_NAME=MetaMCP
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost/metamcp
"""
        
        env_file.write_text(env_content)
        env_example.write_text(env_example_content)
        
        return temp_project, env_file, env_example
    
    def test_env_show(self, temp_env_files):
        """Test env show command."""
        temp_project, env_file, _ = temp_env_files
        
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.project_root = temp_project
            mock_cli_class.return_value = mock_cli
            
            # Mock argparse
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "env"
                mock_args.env_command = "show"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                # Test the command
                with patch('builtins.print') as mock_print:
                    main()
                    # Verify that the env file content was printed
                    mock_print.assert_called()
    
    def test_env_diff(self, temp_env_files):
        """Test env diff command."""
        temp_project, _, _ = temp_env_files
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "1,2c1,2\n< APP_NAME=TestApp\n< DEBUG=true\n---\n> APP_NAME=MetaMCP\n> DEBUG=false"
            mock_run.return_value.stderr = ""
            
            with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
                mock_cli = Mock()
                mock_cli.project_root = temp_project
                mock_cli.run_command = Mock(return_value=0)
                mock_cli_class.return_value = mock_cli
                
                # Mock argparse
                with patch('argparse.ArgumentParser') as mock_parser:
                    mock_args = Mock()
                    mock_args.command = "env"
                    mock_args.env_command = "diff"
                    mock_parser.return_value.parse_args.return_value = mock_args
                    
                    with patch('builtins.print') as mock_print:
                        main()
                        mock_print.assert_called()


class TestDockerCommands:
    """Test Docker-related commands."""
    
    def test_docker_status(self):
        """Test docker status command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.docker_status = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "docker"
                mock_args.docker_command = "status"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.docker_status.assert_called_once()
    
    def test_docker_logs_with_service(self):
        """Test docker logs command with service parameter."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.docker_logs = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "docker"
                mock_args.docker_command = "logs"
                mock_args.service = "metamcp-server"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.docker_logs.assert_called_once_with("metamcp-server")
    
    def test_docker_build_with_no_cache(self):
        """Test docker build command with no-cache flag."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.docker_build = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "docker"
                mock_args.docker_command = "build"
                mock_args.service = "metamcp-server"
                mock_args.no_cache = True
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.docker_build.assert_called_once_with("metamcp-server", True)


class TestDevelopmentCommands:
    """Test development-related commands."""
    
    def test_dev_setup(self):
        """Test dev setup command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.setup_environment = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "dev"
                mock_args.dev_command = "setup"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.setup_environment.assert_called_once()
    
    def test_dev_install(self):
        """Test dev install command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.install_dependencies = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "dev"
                mock_args.dev_command = "install"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.install_dependencies.assert_called_once()


class TestTestingCommands:
    """Test testing-related commands."""
    
    def test_test_unit(self):
        """Test test unit command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.run_tests = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "test"
                mock_args.test_command = "unit"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.run_tests.assert_called_once_with("unit")
    
    def test_test_coverage(self):
        """Test test coverage command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.run_tests = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "test"
                mock_args.test_command = "coverage"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.run_tests.assert_called_once_with("all")


class TestQualityCommands:
    """Test quality-related commands."""
    
    def test_quality_lint(self):
        """Test quality lint command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.lint_code = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "quality"
                mock_args.quality_command = "lint"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.lint_code.assert_called_once()
    
    def test_quality_format(self):
        """Test quality format command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.format_code = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "quality"
                mock_args.quality_command = "format"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.format_code.assert_called_once()


class TestDocumentationCommands:
    """Test documentation-related commands."""
    
    def test_docs_build(self):
        """Test docs build command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.generate_docs = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "docs"
                mock_args.docs_command = "build"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.generate_docs.assert_called_once()
    
    def test_docs_serve(self):
        """Test docs serve command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.serve_docs = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "docs"
                mock_args.docs_command = "serve"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                result = main()
                assert result == 0
                mock_cli.serve_docs.assert_called_once()


class TestUpdateResetCommands:
    """Test update and reset commands."""
    
    def test_update_command(self):
        """Test update command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.run_command = Mock(return_value=0)
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "update"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                with patch('builtins.print') as mock_print:
                    result = main()
                    assert result == 0
                    # Verify that update steps were called
                    assert mock_cli.run_command.call_count >= 2
    
    def test_reset_command(self):
        """Test reset command."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.run_command = Mock(return_value=0)
            mock_cli.project_root = Path("/tmp/test")
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "reset"
                mock_args.hard = False
                mock_parser.return_value.parse_args.return_value = mock_args
                
                with patch('builtins.input', return_value="yes"):
                    with patch('builtins.print') as mock_print:
                        result = main()
                        assert result == 0
                        # Verify that reset steps were called
                        assert mock_cli.run_command.call_count >= 1


class TestParserCreation:
    """Test argument parser creation."""
    
    def test_create_parser(self):
        """Test that the parser is created correctly."""
        parser = create_parser()
        assert parser is not None
        
        # Test that all expected commands are present
        help_text = parser.format_help()
        expected_commands = [
            "validate", "env", "dev", "docker", "monitoring",
            "test", "db", "quality", "docs", "policy", "user",
            "cleanup", "open", "support", "update", "reset", "info"
        ]
        
        for command in expected_commands:
            assert command in help_text
    
    def test_parser_help(self):
        """Test that help is displayed when no command is provided."""
        with patch('argparse.ArgumentParser.print_help') as mock_help:
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                mock_args = Mock()
                mock_args.command = None
                mock_parse.return_value = mock_args
                
                result = main()
                assert result == 1
                mock_help.assert_called_once()


class TestErrorHandling:
    """Test error handling in the CLI."""
    
    def test_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.validate_environment = Mock(side_effect=KeyboardInterrupt())
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "validate"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                with patch('builtins.print') as mock_print:
                    result = main()
                    assert result == 1
                    mock_print.assert_called()
    
    def test_general_exception(self):
        """Test handling of general exceptions."""
        with patch('scripts.cli.MetaMCPCLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli.validate_environment = Mock(side_effect=Exception("Test error"))
            mock_cli_class.return_value = mock_cli
            
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.command = "validate"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                with patch('builtins.print') as mock_print:
                    result = main()
                    assert result == 1
                    mock_print.assert_called()


if __name__ == "__main__":
    pytest.main([__file__]) 