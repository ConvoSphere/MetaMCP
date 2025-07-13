#!/usr/bin/env python3
"""
Test runner for MetaMCP CLI tests.

This script runs all CLI-related tests and provides a comprehensive report.
"""

import sys
import subprocess
import os
from pathlib import Path
import time
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests_with_pytest(test_path, test_type="unit"):
    """Run tests using pytest and return results."""
    print(f"\n{'='*60}")
    print(f"Running {test_type} tests: {test_path}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run pytest with verbose output and JSON report
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_path),
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=none"
        ], capture_output=True, text=True, timeout=300)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("\nSTDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        return {
            "test_type": test_type,
            "test_path": str(test_path),
            "return_code": result.returncode,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print("Test execution timed out after 5 minutes")
        return {
            "test_type": test_type,
            "test_path": str(test_path),
            "return_code": -1,
            "execution_time": 300,
            "stdout": "",
            "stderr": "Test execution timed out",
            "success": False
        }
    except Exception as e:
        print(f"Error running tests: {e}")
        return {
            "test_type": test_type,
            "test_path": str(test_path),
            "return_code": -1,
            "execution_time": 0,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }


def check_test_dependencies():
    """Check if required test dependencies are available."""
    print("Checking test dependencies...")
    
    dependencies = [
        ("pytest", "pytest"),
        ("psutil", "psutil"),
        ("pytest-json-report", "pytest-json-report")
    ]
    
    missing_deps = []
    
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - MISSING")
            missing_deps.append(package_name)
    
    if missing_deps:
        print(f"\nMissing dependencies: {', '.join(missing_deps)}")
        print("Install them with: pip install " + " ".join(missing_deps))
        return False
    
    print("All dependencies available!")
    return True


def run_all_cli_tests():
    """Run all CLI-related tests."""
    print("MetaMCP CLI Test Suite")
    print("=" * 50)
    
    # Check dependencies first
    if not check_test_dependencies():
        print("Cannot run tests due to missing dependencies.")
        return False
    
    # Define test suites
    test_suites = [
        {
            "path": "tests/unit/test_cli.py",
            "type": "unit",
            "description": "CLI Unit Tests"
        },
        {
            "path": "tests/unit/test_cli_utils.py", 
            "type": "unit",
            "description": "CLI Utilities Unit Tests"
        },
        {
            "path": "tests/integration/test_cli_integration.py",
            "type": "integration", 
            "description": "CLI Integration Tests"
        },
        {
            "path": "tests/unit/performance/test_cli_performance.py",
            "type": "performance",
            "description": "CLI Performance Tests"
        }
    ]
    
    results = []
    total_start_time = time.time()
    
    # Run each test suite
    for suite in test_suites:
        test_path = Path(project_root / suite["path"])
        
        if not test_path.exists():
            print(f"\n⚠️  Test file not found: {test_path}")
            results.append({
                "test_type": suite["type"],
                "test_path": str(test_path),
                "return_code": -1,
                "execution_time": 0,
                "stdout": "",
                "stderr": f"Test file not found: {test_path}",
                "success": False
            })
            continue
        
        result = run_tests_with_pytest(test_path, suite["type"])
        result["description"] = suite["description"]
        results.append(result)
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    # Generate summary report
    print_report(results, total_execution_time)
    
    # Save detailed results
    save_test_results(results)
    
    # Return overall success
    return all(result["success"] for result in results)


def print_report(results, total_execution_time):
    """Print a comprehensive test report."""
    print(f"\n{'='*60}")
    print("TEST SUMMARY REPORT")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    
    print(f"Total test suites: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Total execution time: {total_execution_time:.2f} seconds")
    
    print(f"\n{'='*60}")
    print("DETAILED RESULTS")
    print(f"{'='*60}")
    
    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        print(f"{status} | {result['description']}")
        print(f"     Type: {result['test_type']}")
        print(f"     Time: {result['execution_time']:.2f}s")
        print(f"     Code: {result['return_code']}")
        
        if not result["success"] and result["stderr"]:
            print(f"     Error: {result['stderr'][:100]}...")
        print()
    
    # Performance summary
    performance_tests = [r for r in results if r["test_type"] == "performance"]
    if performance_tests:
        print(f"\n{'='*60}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        
        for test in performance_tests:
            if test["success"]:
                print(f"✓ {test['description']}: {test['execution_time']:.2f}s")
            else:
                print(f"✗ {test['description']}: FAILED")


def save_test_results(results):
    """Save detailed test results to a JSON file."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = project_root / "tests" / f"cli_test_results_{timestamp}.json"
    
    # Prepare results for JSON serialization
    json_results = []
    for result in results:
        json_result = {
            "test_type": result["test_type"],
            "test_path": result["test_path"],
            "description": result.get("description", ""),
            "return_code": result["return_code"],
            "execution_time": result["execution_time"],
            "success": result["success"],
            "stdout": result["stdout"][:1000],  # Limit output size
            "stderr": result["stderr"][:1000]   # Limit output size
        }
        json_results.append(json_result)
    
    try:
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
    except Exception as e:
        print(f"Could not save results: {e}")


def main():
    """Main test runner function."""
    print("Starting MetaMCP CLI Test Suite...")
    
    # Change to project root
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        success = run_all_cli_tests()
        
        if success:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error during test execution: {e}")
        return 1
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    sys.exit(main()) 