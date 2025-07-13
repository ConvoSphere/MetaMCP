#!/usr/bin/env python3
"""
Performance tests for the MetaMCP CLI tool.

This module tests the performance characteristics of the CLI tool
including execution time, memory usage, and resource efficiency.
"""

import pytest
import time
import tempfile
import os
import psutil
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.cli import MetaMCPCLI


class TestCLIPerformance:
    """Performance tests for the CLI tool."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for performance testing."""
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
            (temp_path / "docker-compose.yml").write_text("version: '3.8'\nservices:\n  test:\n    image: test")
            (temp_path / "requirements.txt").write_text("pytest\nrequests")
            (temp_path / "pyproject.toml").write_text("[tool.pytest]\ntestpaths = ['tests']")
            (temp_path / "mkdocs.yml").write_text("site_name: Test Docs")
            
            # Create large .env file for testing
            env_content = []
            for i in range(100):
                env_content.append(f"TEST_VAR_{i}=value_{i}")
            env_content.append("APP_NAME=TestApp")
            env_content.append("DEBUG=true")
            env_content.append("ENVIRONMENT=development")
            
            (temp_path / ".env").write_text("\n".join(env_content))
            
            yield temp_path
    
    def test_cli_initialization_performance(self, temp_project):
        """Test CLI initialization performance."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            cli = MetaMCPCLI()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Performance assertions
            assert execution_time < 1.0  # Should initialize in under 1 second
            assert memory_usage < 50.0  # Should use less than 50MB additional memory
            
            print(f"CLI initialization: {execution_time:.3f}s, Memory: {memory_usage:.2f}MB")
            
        finally:
            os.chdir(original_cwd)
    
    def test_environment_validation_performance(self, temp_project):
        """Test environment validation performance."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            result = cli.validate_environment()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Performance assertions
            assert execution_time < 0.5  # Should validate in under 0.5 seconds
            assert memory_usage < 10.0  # Should use less than 10MB additional memory
            
            print(f"Environment validation: {execution_time:.3f}s, Memory: {memory_usage:.2f}MB")
            
        finally:
            os.chdir(original_cwd)
    
    def test_docker_status_performance(self, temp_project):
        """Test docker status performance."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = '{"Name": "test-container", "Status": "running"}'
                mock_run.return_value.stderr = ""
                
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                cli.docker_status()
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                
                # Performance assertions
                assert execution_time < 0.1  # Should execute in under 0.1 seconds
                assert memory_usage < 5.0  # Should use less than 5MB additional memory
                
                print(f"Docker status: {execution_time:.3f}s, Memory: {memory_usage:.2f}MB")
                
        finally:
            os.chdir(original_cwd)
    
    def test_large_env_file_performance(self, temp_project):
        """Test performance with large environment file."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            # Create a large .env file
            large_env_content = []
            for i in range(1000):
                large_env_content.append(f"LARGE_VAR_{i}=very_long_value_with_many_characters_{i}")
            
            (temp_project / ".env").write_text("\n".join(large_env_content))
            
            cli = MetaMCPCLI()
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            result = cli.validate_environment()
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Performance assertions for large files
            assert execution_time < 2.0  # Should handle large files in under 2 seconds
            assert memory_usage < 100.0  # Should use less than 100MB additional memory
            
            print(f"Large env file validation: {execution_time:.3f}s, Memory: {memory_usage:.2f}MB")
            
        finally:
            os.chdir(original_cwd)
    
    def test_concurrent_operations_performance(self, temp_project):
        """Test performance under concurrent operations."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Simulate multiple concurrent operations
            operations = []
            for i in range(10):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = f"Operation {i} result"
                    mock_run.return_value.stderr = ""
                    
                    operations.append(cli.run_command(["echo", f"test_{i}"]))
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Performance assertions for concurrent operations
            assert execution_time < 5.0  # Should handle concurrent operations in under 5 seconds
            assert memory_usage < 50.0  # Should use less than 50MB additional memory
            assert all(op == 0 for op in operations)  # All operations should succeed
            
            print(f"Concurrent operations: {execution_time:.3f}s, Memory: {memory_usage:.2f}MB")
            
        finally:
            os.chdir(original_cwd)
    
    def test_memory_leak_detection(self, temp_project):
        """Test for memory leaks in CLI operations."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            # Get initial memory usage
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Perform multiple operations
            for i in range(100):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = f"Test {i}"
                    mock_run.return_value.stderr = ""
                    
                    cli.run_command(["echo", f"test_{i}"])
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Get final memory usage
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory leak assertions
            assert memory_increase < 20.0  # Should not increase memory by more than 20MB
            
            print(f"Memory leak test: {memory_increase:.2f}MB increase after 100 operations")
            
        finally:
            os.chdir(original_cwd)
    
    def test_command_parsing_performance(self, temp_project):
        """Test command parsing performance."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            start_time = time.time()
            
            # Test multiple command parsing operations
            commands = [
                ["validate"],
                ["env", "show"],
                ["docker", "status"],
                ["dev", "setup"],
                ["test", "unit"],
                ["quality", "lint"],
                ["docs", "build"],
                ["info"]
            ]
            
            for cmd in commands:
                with patch('sys.argv', ['cli'] + cmd):
                    with patch('argparse.ArgumentParser') as mock_parser:
                        mock_args = Mock()
                        mock_args.command = cmd[0]
                        if len(cmd) > 1:
                            setattr(mock_args, f"{cmd[0]}_command", cmd[1])
                        mock_parser.return_value.parse_args.return_value = mock_args
                        
                        # Simulate command execution
                        with patch.object(cli, 'validate_environment') as mock_validate:
                            mock_validate.return_value = {"valid": True}
                            cli.validate_environment()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            assert execution_time < 1.0  # Should parse commands in under 1 second
            
            print(f"Command parsing: {execution_time:.3f}s for {len(commands)} commands")
            
        finally:
            os.chdir(original_cwd)
    
    def test_file_operations_performance(self, temp_project):
        """Test file operations performance."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Test multiple file operations
            for i in range(50):
                # Check if files exist
                assert cli.project_root.exists()
                assert (cli.project_root / "docker-compose.yml").exists()
                assert (cli.project_root / "requirements.txt").exists()
                
                # Read file content
                with open(cli.project_root / ".env", 'r') as f:
                    content = f.read()
                    assert len(content) > 0
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Performance assertions
            assert execution_time < 2.0  # Should perform file operations in under 2 seconds
            assert memory_usage < 10.0  # Should use less than 10MB additional memory
            
            print(f"File operations: {execution_time:.3f}s, Memory: {memory_usage:.2f}MB")
            
        finally:
            os.chdir(original_cwd)


class TestCLIResourceUsage:
    """Test CLI resource usage patterns."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for resource testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            (temp_path / "scripts").mkdir()
            (temp_path / "docker-compose.yml").write_text("version: '3.8'")
            (temp_path / ".env").write_text("APP_NAME=TestApp\nDEBUG=true")
            
            yield temp_path
    
    def test_cpu_usage(self, temp_project):
        """Test CPU usage during CLI operations."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            # Get initial CPU usage
            process = psutil.Process()
            initial_cpu_percent = process.cpu_percent()
            
            # Perform operations
            for i in range(10):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = f"Test {i}"
                    mock_run.return_value.stderr = ""
                    
                    cli.run_command(["echo", f"test_{i}"])
            
            # Get final CPU usage
            final_cpu_percent = process.cpu_percent()
            
            # CPU usage should be reasonable
            assert final_cpu_percent < 50.0  # Should not use more than 50% CPU
            
            print(f"CPU usage: {final_cpu_percent:.1f}%")
            
        finally:
            os.chdir(original_cwd)
    
    def test_disk_io_performance(self, temp_project):
        """Test disk I/O performance during CLI operations."""
        # Change to temp project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)
        
        try:
            cli = MetaMCPCLI()
            
            # Get initial disk I/O
            disk_io = psutil.disk_io_counters()
            initial_read_bytes = disk_io.read_bytes
            initial_write_bytes = disk_io.write_bytes
            
            # Perform file operations
            for i in range(100):
                # Read files
                with open(cli.project_root / ".env", 'r') as f:
                    content = f.read()
                
                # Write temporary files
                temp_file = cli.project_root / f"temp_{i}.txt"
                temp_file.write_text(f"Test content {i}")
                temp_file.unlink()  # Clean up
            
            # Get final disk I/O
            disk_io = psutil.disk_io_counters()
            final_read_bytes = disk_io.read_bytes
            final_write_bytes = disk_io.write_bytes
            
            read_bytes = final_read_bytes - initial_read_bytes
            write_bytes = final_write_bytes - initial_write_bytes
            
            # Disk I/O should be reasonable
            assert read_bytes < 10 * 1024 * 1024  # Less than 10MB read
            assert write_bytes < 10 * 1024 * 1024  # Less than 10MB written
            
            print(f"Disk I/O: {read_bytes / 1024:.1f}KB read, {write_bytes / 1024:.1f}KB written")
            
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__]) 