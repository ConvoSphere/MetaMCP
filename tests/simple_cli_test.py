#!/usr/bin/env python3
"""
Simple CLI test runner without external dependencies.

This script provides basic testing functionality for the CLI tool
without requiring pytest or other external packages.
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import traceback

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.cli import MetaMCPCLI
except ImportError as e:
    print(f"Error importing CLI module: {e}")
    sys.exit(1)


class SimpleTestRunner:
    """Simple test runner without external dependencies."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results."""
        self.tests_run += 1
        start_time = time.time()
        
        try:
            test_func()
            execution_time = time.time() - start_time
            self.tests_passed += 1
            self.results.append({
                "name": test_name,
                "status": "PASS",
                "execution_time": execution_time,
                "error": None
            })
            print(f"✓ {test_name} ({execution_time:.3f}s)")
            return True
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.tests_failed += 1
            self.results.append({
                "name": test_name,
                "status": "FAIL",
                "execution_time": execution_time,
                "error": str(e)
            })
            print(f"✗ {test_name} ({execution_time:.3f}s)")
            print(f"  Error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_failed > 0:
            print(f"\nFAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['name']}: {result['error']}")


def test_cli_initialization():
    """Test CLI initialization."""
    cli = MetaMCPCLI()
    assert cli.project_root.exists()
    assert cli.scripts_dir.exists()


def test_run_command_success():
    """Test successful command execution."""
    cli = MetaMCPCLI()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        
        result = cli.run_command(["echo", "test"])
        assert result == 0


def test_run_command_failure():
    """Test failed command execution."""
    cli = MetaMCPCLI()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Error"
        
        result = cli.run_command(["invalid", "command"])
        assert result == 1


def test_environment_validation():
    """Test environment validation."""
    cli = MetaMCPCLI()
    
    with patch('os.getenv') as mock_getenv:
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
            "ADMIN_PORT": "8501"
        }.get(key, default)
        
        result = cli.validate_environment()
        assert result["valid"] is True


def test_docker_status():
    """Test docker status command."""
    cli = MetaMCPCLI()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"Name": "test-container", "Status": "running"}'
        mock_run.return_value.stderr = ""
        
        with patch('builtins.print') as mock_print:
            cli.docker_status()
            mock_print.assert_called()


def test_docker_logs():
    """Test docker logs command."""
    cli = MetaMCPCLI()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Container logs here"
        mock_run.return_value.stderr = ""
        
        with patch('builtins.print') as mock_print:
            cli.docker_logs("test-service")
            mock_print.assert_called()


def test_dev_setup():
    """Test dev setup command."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        result = cli.setup_environment()
        assert result == 0


def test_dev_install():
    """Test dev install command."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        result = cli.install_dependencies()
        assert result == 0


def test_run_tests():
    """Test test execution."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        result = cli.run_tests("unit")
        assert result == 0


def test_lint_code():
    """Test code linting."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        result = cli.lint_code()
        assert result == 0


def test_generate_docs():
    """Test documentation generation."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        result = cli.generate_docs()
        assert result == 0


def test_show_project_info():
    """Test project info display."""
    cli = MetaMCPCLI()
    
    with patch('builtins.print') as mock_print:
        cli.show_project_info()
        mock_print.assert_called()


def test_update_project():
    """Test project update."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        with patch('builtins.print') as mock_print:
            cli.update_project()
            mock_print.assert_called()


def test_reset_project():
    """Test project reset."""
    cli = MetaMCPCLI()
    
    with patch.object(cli, 'run_command') as mock_run:
        mock_run.return_value = 0
        
        with patch('builtins.input', return_value="yes"):
            with patch('builtins.print') as mock_print:
                cli.reset_project(hard=False)
                mock_print.assert_called()


def test_error_handling():
    """Test error handling."""
    cli = MetaMCPCLI()
    
    with patch('subprocess.run', side_effect=Exception("Test error")):
        result = cli.run_command(["echo", "test"])
        assert result == 1


def test_missing_files():
    """Test handling of missing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create minimal structure
        (temp_path / "scripts").mkdir()
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_path)
        
        try:
            cli = MetaMCPCLI()
            
            # Test environment validation with missing .env
            result = cli.validate_environment()
            
            # Should detect missing .env file
            assert result["valid"] is False
            assert len(result["missing_required"]) > 0
            
        finally:
            os.chdir(original_cwd)


def main():
    """Run all tests."""
    print("MetaMCP CLI Simple Test Suite")
    print("=" * 50)
    
    runner = SimpleTestRunner()
    
    # Define all tests
    tests = [
        ("CLI Initialization", test_cli_initialization),
        ("Run Command Success", test_run_command_success),
        ("Run Command Failure", test_run_command_failure),
        ("Environment Validation", test_environment_validation),
        ("Docker Status", test_docker_status),
        ("Docker Logs", test_docker_logs),
        ("Dev Setup", test_dev_setup),
        ("Dev Install", test_dev_install),
        ("Run Tests", test_run_tests),
        ("Lint Code", test_lint_code),
        ("Generate Docs", test_generate_docs),
        ("Show Project Info", test_show_project_info),
        ("Update Project", test_update_project),
        ("Reset Project", test_reset_project),
        ("Error Handling", test_error_handling),
        ("Missing Files", test_missing_files),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        runner.run_test(test_name, test_func)
    
    # Print summary
    runner.print_summary()
    
    # Return appropriate exit code
    return 0 if runner.tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main()) 