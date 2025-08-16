"""
Policy Testing Tools

This module provides tools for testing and validating policies,
including policy syntax checking, test case execution, and
policy coverage analysis.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..utils.logging import get_logger
from .policies import PolicyEngine

logger = get_logger(__name__)


@dataclass
class PolicyTestCase:
    """Policy test case definition."""

    name: str
    description: str
    input_data: dict[str, Any]
    expected_result: bool
    expected_reason: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class PolicyTestResult:
    """Policy test result."""

    test_case: PolicyTestCase
    actual_result: bool
    passed: bool
    execution_time: float
    actual_reason: str | None = None
    error_message: str | None = None


@dataclass
class PolicyCoverage:
    """Policy coverage information."""

    policy_name: str
    total_rules: int
    covered_rules: int
    coverage_percentage: float
    uncovered_rules: list[str] = field(default_factory=list)


class PolicyTester:
    """
    Policy testing and validation tool.

    This class provides comprehensive testing capabilities for policies,
    including syntax validation, test case execution, and coverage analysis.
    """

    def __init__(self, policy_engine: PolicyEngine):
        """
        Initialize Policy Tester.

        Args:
            policy_engine: Policy engine instance to test
        """
        self.policy_engine = policy_engine
        self.test_cases: dict[str, list[PolicyTestCase]] = {}
        self.test_results: list[PolicyTestResult] = []

    async def validate_policy_syntax(
        self, policy_content: str
    ) -> tuple[bool, list[str]]:
        """
        Validate policy syntax.

        Args:
            policy_content: Policy content to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            # Basic Rego syntax validation
            if not policy_content.strip():
                errors.append("Policy content is empty")
                return False, errors

            # Check for required package declaration
            if not re.search(r"package\s+\w+", policy_content):
                errors.append("Missing package declaration")

            # Check for basic Rego structure
            if not re.search(r"default\s+\w+\s*=", policy_content) and not re.search(
                r"\w+\s*\{", policy_content
            ):
                errors.append("Missing rule definitions")

            # Check for balanced braces
            brace_count = policy_content.count("{") - policy_content.count("}")
            if brace_count != 0:
                errors.append(
                    f"Unbalanced braces: {brace_count} extra {'{' if brace_count > 0 else '}'}"
                )

            # Check for common syntax errors
            if re.search(r"[a-zA-Z_]\w*\s*\{[^}]*$", policy_content, re.MULTILINE):
                errors.append("Unclosed rule definition")

            # Validate input references
            input_refs = re.findall(r"input\.\w+", policy_content)
            for ref in input_refs:
                if not re.match(r"input\.\w+(\[\w+\])?(\.[\w\[\]]+)*", ref):
                    errors.append(f"Invalid input reference: {ref}")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Syntax validation error: {str(e)}")
            return False, errors

    async def add_test_case(self, policy_name: str, test_case: PolicyTestCase) -> None:
        """
        Add a test case for a policy.

        Args:
            policy_name: Name of the policy to test
            test_case: Test case to add
        """
        if policy_name not in self.test_cases:
            self.test_cases[policy_name] = []

        self.test_cases[policy_name].append(test_case)
        logger.info(f"Added test case '{test_case.name}' for policy '{policy_name}'")

    async def add_predefined_test_cases(self) -> None:
        """Add predefined test cases for common scenarios."""

        # Tool access test cases
        tool_access_tests = [
            PolicyTestCase(
                name="user_can_read_tool",
                description="User should be able to read tools",
                input_data={
                    "user": {"id": "user1", "role": "user"},
                    "resource": "tool:calculator",
                    "action": "read",
                },
                expected_result=True,
                tags=["tool_access", "positive"],
            ),
            PolicyTestCase(
                name="user_cannot_manage_tool",
                description="Regular user should not be able to manage tools",
                input_data={
                    "user": {"id": "user1", "role": "user"},
                    "resource": "tool:calculator",
                    "action": "manage",
                },
                expected_result=False,
                tags=["tool_access", "negative"],
            ),
            PolicyTestCase(
                name="admin_can_manage_tool",
                description="Admin should be able to manage tools",
                input_data={
                    "user": {"id": "admin1", "role": "admin"},
                    "resource": "tool:calculator",
                    "action": "manage",
                },
                expected_result=True,
                tags=["tool_access", "positive", "admin"],
            ),
            PolicyTestCase(
                name="user_can_execute_tool_with_permission",
                description="User with tool_execute permission can execute tools",
                input_data={
                    "user": {
                        "id": "user1",
                        "role": "user",
                        "permissions": ["tool_execute"],
                    },
                    "resource": "tool:calculator",
                    "action": "execute",
                },
                expected_result=True,
                tags=["tool_access", "positive", "permissions"],
            ),
            PolicyTestCase(
                name="user_cannot_execute_tool_without_permission",
                description="User without tool_execute permission cannot execute tools",
                input_data={
                    "user": {"id": "user1", "role": "user", "permissions": []},
                    "resource": "tool:calculator",
                    "action": "execute",
                },
                expected_result=False,
                tags=["tool_access", "negative", "permissions"],
            ),
        ]

        for test_case in tool_access_tests:
            await self.add_test_case("tool_access", test_case)

        # Rate limiting test cases
        rate_limiting_tests = [
            PolicyTestCase(
                name="rate_limit_not_exceeded",
                description="Request within rate limit should be allowed",
                input_data={
                    "request_count": 50,
                    "limit": 100,
                    "window_start": datetime.utcnow().timestamp(),
                },
                expected_result=True,
                tags=["rate_limiting", "positive"],
            ),
            PolicyTestCase(
                name="rate_limit_exceeded",
                description="Request exceeding rate limit should be denied",
                input_data={
                    "request_count": 150,
                    "limit": 100,
                    "window_start": datetime.utcnow().timestamp(),
                },
                expected_result=False,
                tags=["rate_limiting", "negative"],
            ),
        ]

        for test_case in rate_limiting_tests:
            await self.add_test_case("rate_limiting", test_case)

        # Data access test cases
        data_access_tests = [
            PolicyTestCase(
                name="user_can_read_public_data",
                description="User should be able to read public data",
                input_data={
                    "user": {"id": "user1", "role": "user"},
                    "resource": "data:public:config",
                    "action": "read",
                },
                expected_result=True,
                tags=["data_access", "positive"],
            ),
            PolicyTestCase(
                name="user_can_read_own_data",
                description="User should be able to read their own data",
                input_data={
                    "user": {"id": "user1", "role": "user"},
                    "resource": "data:user:user1:profile",
                    "action": "read",
                    "resource_user_id": "user1",
                },
                expected_result=True,
                tags=["data_access", "positive"],
            ),
            PolicyTestCase(
                name="user_cannot_read_other_user_data",
                description="User should not be able to read other user's data",
                input_data={
                    "user": {"id": "user1", "role": "user"},
                    "resource": "data:user:user2:profile",
                    "action": "read",
                    "resource_user_id": "user2",
                },
                expected_result=False,
                tags=["data_access", "negative"],
            ),
            PolicyTestCase(
                name="user_can_write_own_data_with_permission",
                description="User with data_write permission can write their own data",
                input_data={
                    "user": {
                        "id": "user1",
                        "role": "user",
                        "permissions": ["data_write"],
                    },
                    "resource": "data:user:user1:profile",
                    "action": "write",
                    "resource_user_id": "user1",
                },
                expected_result=True,
                tags=["data_access", "positive", "permissions"],
            ),
        ]

        for test_case in data_access_tests:
            await self.add_test_case("data_access", test_case)

        logger.info("Added predefined test cases")

    async def run_test_case(
        self, test_case: PolicyTestCase, policy_name: str
    ) -> PolicyTestResult:
        """
        Run a single test case.

        Args:
            test_case: Test case to run
            policy_name: Name of the policy to test

        Returns:
            Test result
        """
        import time

        start_time = time.time()

        try:
            # Extract user, resource, and action from input data
            user_id = test_case.input_data.get("user", {}).get("id", "anonymous")
            resource = test_case.input_data.get("resource", "")
            action = test_case.input_data.get("action", "")

            # Create context from input data
            context = {
                k: v
                for k, v in test_case.input_data.items()
                if k not in ["user", "resource", "action"]
            }

            # Run the policy check
            actual_result = await self.policy_engine.check_access(
                user_id=user_id, resource=resource, action=action, context=context
            )

            execution_time = time.time() - start_time

            # Determine if test passed
            passed = actual_result == test_case.expected_result

            return PolicyTestResult(
                test_case=test_case,
                actual_result=actual_result,
                passed=passed,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time

            return PolicyTestResult(
                test_case=test_case,
                actual_result=False,
                passed=False,
                execution_time=execution_time,
                error_message=str(e),
            )

    async def run_policy_tests(self, policy_name: str) -> list[PolicyTestResult]:
        """
        Run all test cases for a specific policy.

        Args:
            policy_name: Name of the policy to test

        Returns:
            List of test results
        """
        if policy_name not in self.test_cases:
            logger.warning(f"No test cases found for policy: {policy_name}")
            return []

        results = []
        logger.info(
            f"Running {len(self.test_cases[policy_name])} test cases for policy: {policy_name}"
        )

        for test_case in self.test_cases[policy_name]:
            result = await self.run_test_case(test_case, policy_name)
            results.append(result)
            self.test_results.append(result)

        return results

    async def run_all_tests(self) -> dict[str, list[PolicyTestResult]]:
        """
        Run all test cases for all policies.

        Returns:
            Dictionary mapping policy names to test results
        """
        all_results = {}

        for policy_name in self.test_cases.keys():
            results = await self.run_policy_tests(policy_name)
            all_results[policy_name] = results

        return all_results

    async def generate_test_report(
        self, results: list[PolicyTestResult]
    ) -> dict[str, Any]:
        """
        Generate a test report from test results.

        Args:
            results: List of test results

        Returns:
            Test report dictionary
        """
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests

        # Group by policy
        policy_results = {}
        for result in results:
            policy_name = result.test_case.name.split("_")[
                0
            ]  # Extract policy name from test name
            if policy_name not in policy_results:
                policy_results[policy_name] = []
            policy_results[policy_name].append(result)

        # Calculate coverage
        coverage = await self.calculate_policy_coverage()

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (
                    (passed_tests / total_tests * 100) if total_tests > 0 else 0
                ),
                "execution_time": sum(r.execution_time for r in results),
            },
            "policy_results": policy_results,
            "coverage": coverage,
            "failed_tests": [r for r in results if not r.passed],
            "generated_at": datetime.utcnow().isoformat(),
        }

        return report

    async def calculate_policy_coverage(self) -> list[PolicyCoverage]:
        """
        Calculate policy coverage based on test cases.

        Returns:
            List of policy coverage information
        """
        coverage_list = []

        for policy_name, test_cases in self.test_cases.items():
            # This is a simplified coverage calculation
            # In a real implementation, this would analyze the actual policy rules
            total_rules = 5  # Estimated number of rules per policy
            covered_rules = min(len(test_cases), total_rules)
            coverage_percentage = (
                (covered_rules / total_rules * 100) if total_rules > 0 else 0
            )

            coverage = PolicyCoverage(
                policy_name=policy_name,
                total_rules=total_rules,
                covered_rules=covered_rules,
                coverage_percentage=coverage_percentage,
            )

            coverage_list.append(coverage)

        return coverage_list

    async def validate_policy_with_tests(
        self, policy_content: str, policy_name: str
    ) -> tuple[bool, list[str]]:
        """
        Validate a policy using test cases.

        Args:
            policy_content: Policy content to validate
            policy_name: Name of the policy

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # First, validate syntax
        syntax_valid, syntax_errors = await self.validate_policy_syntax(policy_content)
        if not syntax_valid:
            errors.extend(syntax_errors)
            return False, errors

        # Then, run tests if available
        if policy_name in self.test_cases:
            results = await self.run_policy_tests(policy_name)
            failed_tests = [r for r in results if not r.passed]

            if failed_tests:
                errors.append(f"{len(failed_tests)} test cases failed")
                for result in failed_tests:
                    errors.append(
                        f"  - {result.test_case.name}: expected {result.test_case.expected_result}, got {result.actual_result}"
                    )

        return len(errors) == 0, errors

    async def export_test_results(self, format: str = "json") -> str:
        """
        Export test results in specified format.

        Args:
            format: Export format (json, csv, html)

        Returns:
            Exported test results
        """
        if format.lower() == "json":
            report = await self.generate_test_report(self.test_results)
            return json.dumps(report, indent=2, default=str)

        elif format.lower() == "csv":
            csv_lines = ["Test Name,Policy,Expected,Actual,Passed,Execution Time,Error"]
            for result in self.test_results:
                csv_lines.append(
                    f"{result.test_case.name},{result.test_case.name.split('_')[0]},{result.test_case.expected_result},{result.actual_result},{result.passed},{result.execution_time},{result.error_message or ''}"
                )
            return "\n".join(csv_lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def create_test_case_from_example(
        self,
        policy_name: str,
        example_name: str,
        input_data: dict[str, Any],
        expected_result: bool,
    ) -> PolicyTestCase:
        """
        Create a test case from an example.

        Args:
            policy_name: Name of the policy
            example_name: Name for the test case
            input_data: Input data for the test
            expected_result: Expected result

        Returns:
            Created test case
        """
        test_case = PolicyTestCase(
            name=example_name,
            description=f"Test case for {policy_name}: {example_name}",
            input_data=input_data,
            expected_result=expected_result,
            tags=[policy_name, "example"],
        )

        await self.add_test_case(policy_name, test_case)
        return test_case

    async def get_test_statistics(self) -> dict[str, Any]:
        """
        Get test statistics.

        Returns:
            Test statistics dictionary
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests

        # Group by tags
        tag_stats = {}
        for result in self.test_results:
            for tag in result.test_case.tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {"total": 0, "passed": 0, "failed": 0}
                tag_stats[tag]["total"] += 1
                if result.passed:
                    tag_stats[tag]["passed"] += 1
                else:
                    tag_stats[tag]["failed"] += 1

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
            "average_execution_time": (
                sum(r.execution_time for r in self.test_results) / total_tests
                if total_tests > 0
                else 0
            ),
            "tag_statistics": tag_stats,
        }
