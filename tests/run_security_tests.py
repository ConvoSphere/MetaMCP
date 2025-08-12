#!/usr/bin/env python3
"""
Security Test Runner

This script runs all security-related tests to verify that
the implemented security features are working correctly.
"""

import sys
import subprocess
import time
from pathlib import Path


def run_tests(test_path: str, test_type: str) -> bool:
    """
    Run tests for a specific security component.

    Args:
        test_path: Path to test file
        test_type: Type of test being run

    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\n🔒 Running {test_type} tests...")
    print(f"📁 Test file: {test_path}")

    try:
        # Run pytest with verbose output
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                test_path,
                "-v",
                "--tb=short",
                "--color=yes",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print(f"✅ {test_type} tests PASSED")
            print(f"📊 Output:\n{result.stdout}")
            return True
        else:
            print(f"❌ {test_type} tests FAILED")
            print(f"📊 Output:\n{result.stdout}")
            print(f"🚨 Errors:\n{result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {test_type} tests TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {test_type} tests ERROR: {e}")
        return False


def main():
    """Main test runner function."""
    print("🚀 Starting Security Test Suite")
    print("=" * 50)

    # Define test files and their types
    tests = [
        ("tests/unit/security/test_api_keys.py", "API Key Management"),
        ("tests/unit/security/test_tool_registry.py", "Tool Registry Security"),
        ("tests/unit/security/test_resource_limits.py", "Resource Limits"),
        ("tests/unit/security/test_api_versioning.py", "API Versioning"),
        ("tests/integration/test_security_integration.py", "Security Integration"),
    ]

    # Track results
    results = {}
    start_time = time.time()

    # Run each test
    for test_path, test_type in tests:
        if Path(test_path).exists():
            success = run_tests(test_path, test_type)
            results[test_type] = success
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results[test_type] = False

    # Calculate summary
    end_time = time.time()
    total_time = end_time - start_time

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    # Print summary
    print("\n" + "=" * 50)
    print("📋 SECURITY TEST SUMMARY")
    print("=" * 50)

    for test_type, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_type:<25} {status}")

    print(f"\n📊 Results: {passed}/{total} test suites passed")
    print(f"⏱️  Total time: {total_time:.2f} seconds")

    if passed == total:
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        print("🔒 Security features are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        print("🔧 Please review the failed tests and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
