#!/usr/bin/env python3
"""
Test Utilities for MetaMCP

This module provides test-related utilities for the MetaMCP project.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any


class TestUtils:
    """Test utilities for MetaMCP project management."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> int:
        """Run a shell command and return exit code."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode
        except Exception as e:
            print(f"Error running command: {e}", file=sys.stderr)
            return 1
    
    def check_test_dependencies(self) -> Dict[str, bool]:
        """Check if test dependencies are available."""
        dependencies = {}
        
        # Check pytest
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True
            )
            dependencies["pytest"] = result.returncode == 0
        except Exception:
            dependencies["pytest"] = False
        
        # Check coverage
        try:
            result = subprocess.run(
                [sys.executable, "-m", "coverage", "--version"],
                capture_output=True,
                text=True
            )
            dependencies["coverage"] = result.returncode == 0
        except Exception:
            dependencies["coverage"] = False
        
        # Check flake8
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "--version"],
                capture_output=True,
                text=True
            )
            dependencies["flake8"] = result.returncode == 0
        except Exception:
            dependencies["flake8"] = False
        
        # Check black
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--version"],
                capture_output=True,
                text=True
            )
            dependencies["black"] = result.returncode == 0
        except Exception:
            dependencies["black"] = False
        
        # Check bandit
        try:
            result = subprocess.run(
                [sys.executable, "-m", "bandit", "--version"],
                capture_output=True,
                text=True
            )
            dependencies["bandit"] = result.returncode == 0
        except Exception:
            dependencies["bandit"] = False
        
        return dependencies
    
    def run_unit_tests(self, coverage: bool = True, verbose: bool = False) -> int:
        """Run unit tests."""
        print("🧪 Running unit tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/unit/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=metamcp", "--cov-report=html", "--cov-report=term"])
        
        return self.run_command(cmd)
    
    def run_integration_tests(self, coverage: bool = False, verbose: bool = False) -> int:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/integration/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=metamcp", "--cov-report=html", "--cov-report=term"])
        
        return self.run_command(cmd)
    
    def run_blackbox_tests(self, verbose: bool = False) -> int:
        """Run blackbox tests."""
        print("📦 Running blackbox tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/blackbox/"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd)
    
    def run_performance_tests(self, verbose: bool = False) -> int:
        """Run performance tests."""
        print("⚡ Running performance tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/unit/performance/"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd)
    
    def run_security_tests(self, verbose: bool = False) -> int:
        """Run security tests."""
        print("🔒 Running security tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/unit/security/"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd)
    
    def run_all_tests(self, coverage: bool = True, verbose: bool = False) -> int:
        """Run all tests."""
        print("🧪 Running all tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=metamcp", "--cov-report=html", "--cov-report=term"])
        
        return self.run_command(cmd)
    
    def run_linting(self) -> int:
        """Run code linting with flake8."""
        print("🔍 Running code linting...")
        return self.run_command([sys.executable, "-m", "flake8", "metamcp/"])
    
    def run_formatting(self) -> int:
        """Run code formatting with black."""
        print("🎨 Running code formatting...")
        return self.run_command([sys.executable, "-m", "black", "metamcp/"])
    
    def run_security_checks(self) -> int:
        """Run security checks with bandit."""
        print("🔒 Running security checks...")
        return self.run_command([sys.executable, "-m", "bandit", "-r", "metamcp/"])
    
    def run_type_checking(self) -> int:
        """Run type checking with mypy."""
        print("🔍 Running type checking...")
        return self.run_command([sys.executable, "-m", "mypy", "metamcp/"])
    
    def generate_test_report(self) -> int:
        """Generate a comprehensive test report."""
        print("📊 Generating test report...")
        
        # Run tests with coverage
        result = self.run_all_tests(coverage=True, verbose=False)
        
        if result == 0:
            print("✅ Test report generated successfully")
            print("📁 Coverage report available in htmlcov/index.html")
        
        return result
    
    def check_test_coverage(self, min_coverage: float = 80.0) -> bool:
        """Check if test coverage meets minimum requirements."""
        print(f"📊 Checking test coverage (minimum: {min_coverage}%)...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "coverage", "report", "--show-missing"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                # Parse coverage output to get total coverage
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'TOTAL' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                coverage = float(parts[-1].rstrip('%'))
                                meets_requirement = coverage >= min_coverage
                                print(f"   Coverage: {coverage:.1f}% {'✅' if meets_requirement else '❌'}")
                                return meets_requirement
                            except ValueError:
                                pass
            
            print("❌ Could not parse coverage report")
            return False
            
        except Exception as e:
            print(f"❌ Error checking coverage: {e}")
            return False


def main():
    """Test the test utilities."""
    project_root = Path(__file__).parent.parent
    test_utils = TestUtils(project_root)
    
    print("🧪 Test Utilities Test")
    print("=" * 40)
    
    # Check dependencies
    dependencies = test_utils.check_test_dependencies()
    print("Dependencies:")
    for dep, available in dependencies.items():
        status_icon = "✅" if available else "❌"
        print(f"  {status_icon} {dep}")
    
    # Check test directories
    test_dirs = ["tests/unit", "tests/integration", "tests/blackbox"]
    print("\nTest directories:")
    for test_dir in test_dirs:
        dir_path = project_root / test_dir
        exists = dir_path.exists()
        status_icon = "✅" if exists else "❌"
        print(f"  {status_icon} {test_dir}")


if __name__ == "__main__":
    main() 