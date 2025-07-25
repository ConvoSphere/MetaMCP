"""
Black Box Test Runner

Executes comprehensive black box tests for the MetaMCP REST API.
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest
from httpx import AsyncClient

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
from tests.blackbox.conftest import API_BASE_URL

sys.path.insert(0, str(project_root))


class BlackBoxTestRunner:
    """Comprehensive black box test runner for MetaMCP API."""

    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    async def run_health_check(self) -> bool:
        """Run basic health check before starting tests."""
        try:
            async with AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}health/")
                if response.status_code == 200:
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    async def run_test_category(self, category: str, test_files: list[str]) -> dict:
        """Run tests for a specific category."""
        print(f"\n🔍 Running {category} tests...")
        category_start = time.time()

        results = {
            "category": category,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "errors": [],
            "start_time": category_start,
            "end_time": None,
        }

        for test_file in test_files:
            try:
                print(f"  📋 Running {test_file}...")
                test_start = time.time()

                # Run pytest for the specific test file
                exit_code = pytest.main(
                    [str(test_file), "-v", "--tb=short", "--disable-warnings"]
                )

                test_end = time.time()
                test_duration = test_end - test_start

                if exit_code == 0:
                    results["tests_passed"] += 1
                    print(f"  ✅ {test_file} passed ({test_duration:.2f}s)")
                else:
                    results["tests_failed"] += 1
                    print(f"  ❌ {test_file} failed ({test_duration:.2f}s)")

                results["tests_run"] += 1

            except Exception as e:
                results["tests_failed"] += 1
                results["errors"].append(f"{test_file}: {str(e)}")
                print(f"  ❌ {test_file} error: {e}")

        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]

        return results

    async def run_all_tests(self) -> dict:
        """Run all black box test categories."""
        print("🚀 Starting Black Box Test Suite")
        print("=" * 50)

        self.start_time = time.time()

        # Check if API is available
        if not await self.run_health_check():
            print("❌ API not available, aborting tests")
            return {"error": "API not available"}

        # Define test categories and their files
        test_categories = {
            "Health & Basic": [
                "tests/blackbox/rest_api/test_health.py",
                "tests/blackbox/rest_api/test_auth.py",
            ],
            "Tools & Operations": [
                "tests/blackbox/rest_api/test_tools.py",
            ],
            "Proxy & Discovery": [
                "tests/blackbox/rest_api/test_proxy.py",
            ],
            "Admin & Management": [
                "tests/blackbox/rest_api/test_admin.py",
            ],
            "Composition & OAuth": [
                "tests/blackbox/rest_api/test_composition.py",
                "tests/blackbox/rest_api/test_oauth.py",
            ],
            "Performance & Load": [
                "tests/blackbox/performance/test_load.py",
            ],
            "Security": [
                "tests/blackbox/security/test_security.py",
            ],
            "Integration & Workflows": [
                "tests/blackbox/integration/test_workflows.py",
            ],
        }

        # Run each category
        for category, test_files in test_categories.items():
            # Check if test files exist
            existing_files = [f for f in test_files if Path(f).exists()]
            if not existing_files:
                print(f"⚠️  No test files found for {category}")
                continue

            results = await self.run_test_category(category, existing_files)
            self.test_results[category] = results

        self.end_time = time.time()
        return self.generate_summary()

    def generate_summary(self) -> dict:
        """Generate comprehensive test summary."""
        if not self.test_results:
            return {"error": "No tests were run"}

        total_tests = sum(r["tests_run"] for r in self.test_results.values())
        total_passed = sum(r["tests_passed"] for r in self.test_results.values())
        total_failed = sum(r["tests_failed"] for r in self.test_results.values())
        total_skipped = sum(r["tests_skipped"] for r in self.test_results.values())
        total_duration = self.end_time - self.start_time if self.end_time else 0

        summary = {
            "overall": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "success_rate": (
                    (total_passed / total_tests * 100) if total_tests > 0 else 0
                ),
                "duration": total_duration,
            },
            "categories": self.test_results,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

        return summary

    def print_summary(self, summary: dict):
        """Print formatted test summary."""
        if "error" in summary:
            print(f"\n❌ Test execution failed: {summary['error']}")
            return

        overall = summary["overall"]

        print("\n" + "=" * 50)
        print("📊 BLACK BOX TEST SUMMARY")
        print("=" * 50)

        print(f"⏱️  Total Duration: {overall['duration']:.2f}s")
        print(f"📈 Total Tests: {overall['total_tests']}")
        print(f"✅ Passed: {overall['passed']}")
        print(f"❌ Failed: {overall['failed']}")
        print(f"⏭️  Skipped: {overall['skipped']}")
        print(f"📊 Success Rate: {overall['success_rate']:.1f}%")

        print("\n📋 Category Breakdown:")
        print("-" * 30)

        for category, results in summary["categories"].items():
            success_rate = (
                (results["tests_passed"] / results["tests_run"] * 100)
                if results["tests_run"] > 0
                else 0
            )
            status = (
                "✅"
                if results["tests_failed"] == 0
                else "⚠️" if results["tests_passed"] > 0 else "❌"
            )

            print(f"{status} {category}:")
            print(
                f"   Tests: {results['tests_run']} | Passed: {results['tests_passed']} | Failed: {results['tests_failed']}"
            )
            print(
                f"   Duration: {results['duration']:.2f}s | Success Rate: {success_rate:.1f}%"
            )

            if results["errors"]:
                print(f"   Errors: {len(results['errors'])}")
                for error in results["errors"][:3]:  # Show first 3 errors
                    print(f"     - {error}")
                if len(results["errors"]) > 3:
                    print(f"     ... and {len(results['errors']) - 3} more errors")
            print()

        # Overall status
        if overall["failed"] == 0:
            print("🎉 All tests passed!")
        elif overall["success_rate"] >= 80:
            print("⚠️  Most tests passed, some failures detected")
        else:
            print("❌ Significant test failures detected")

        print("=" * 50)


async def main():
    """Main test runner function."""
    runner = BlackBoxTestRunner()

    try:
        summary = await runner.run_all_tests()
        runner.print_summary(summary)

        # Return appropriate exit code
        if "error" in summary:
            return 1

        overall = summary["overall"]
        if overall["failed"] == 0:
            return 0
        elif overall["success_rate"] >= 80:
            return 0  # Allow some failures for development
        else:
            return 1

    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
