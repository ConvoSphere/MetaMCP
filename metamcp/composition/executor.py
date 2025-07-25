"""
Workflow Executor

This module provides the workflow step executor for handling
individual step execution with retry logic and error handling.
"""

import asyncio
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ..exceptions import WorkflowExecutionError
from ..utils.logging import get_logger
from .models import (
    StepExecutionResult,
    StepStatus,
    StepType,
    WorkflowStep,
)

logger = get_logger(__name__)


class WorkflowExecutor:
    """
    Executor for individual workflow steps.

    This class handles the execution of individual workflow steps
    with retry logic, timeout handling, and error management.
    """

    def __init__(self):
        """Initialize the workflow executor."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow executor."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Workflow Executor...")
            self._initialized = True
            logger.info("Workflow Executor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Workflow Executor: {e}")
            raise WorkflowExecutionError(f"Initialization failed: {str(e)}")

    async def execute_step(
        self,
        step: WorkflowStep,
        tool_executor: Callable,
        variables: dict[str, Any],
        timeout: int | None = None,
    ) -> StepExecutionResult:
        """
        Execute a single workflow step.

        Args:
            step: Workflow step to execute
            tool_executor: Function to execute tools
            variables: Workflow variables
            timeout: Step timeout in seconds

        Returns:
            Step execution result
        """
        start_time = time.time()
        step_start_time = datetime.now(UTC)

        try:
            logger.info(f"Executing step: {step.id} ({step.step_type})")

            # Execute step based on type
            if step.step_type == StepType.TOOL_CALL:
                result = await self._execute_tool_step(
                    step, tool_executor, variables, timeout
                )
            elif step.step_type == StepType.CONDITION:
                result = await self._execute_condition_step(step, variables)
            elif step.step_type == StepType.PARALLEL:
                result = await self._execute_parallel_step(
                    step, tool_executor, variables, timeout
                )
            elif step.step_type == StepType.LOOP:
                result = await self._execute_loop_step(
                    step, tool_executor, variables, timeout
                )
            elif step.step_type == StepType.DELAY:
                result = await self._execute_delay_step(step)
            elif step.step_type == StepType.HTTP_REQUEST:
                result = await self._execute_http_step(step, variables, timeout)
            else:
                raise WorkflowExecutionError(f"Unsupported step type: {step.step_type}")

            # Calculate execution time
            execution_time = time.time() - start_time
            step_end_time = datetime.now(UTC)

            logger.info(f"Step {step.id} completed in {execution_time:.2f}s")

            return StepExecutionResult(
                step_id=step.id,
                status=StepStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                started_at=step_start_time,
                completed_at=step_end_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            step_end_time = datetime.now(UTC)

            logger.error(f"Step {step.id} failed: {e}")

            return StepExecutionResult(
                step_id=step.id,
                status=StepStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
                started_at=step_start_time,
                completed_at=step_end_time,
            )

    async def _execute_tool_step(
        self,
        step: WorkflowStep,
        tool_executor: Callable,
        variables: dict[str, Any],
        timeout: int | None,
    ) -> Any:
        """Execute a tool call step."""
        tool_name = step.config.get("tool_name")
        if not tool_name:
            raise WorkflowExecutionError(f"Tool name not specified for step {step.id}")

        # Prepare arguments with variable substitution
        arguments = self._substitute_variables(
            step.config.get("arguments", {}), variables
        )

        # Execute tool with retry logic
        retry_config = step.retry_config or {}
        max_attempts = retry_config.get("max_attempts", 1)
        initial_delay = retry_config.get("initial_delay", 1.0)
        backoff_factor = retry_config.get("backoff_factor", 2.0)

        for attempt in range(max_attempts):
            try:
                if timeout:
                    result = await asyncio.wait_for(
                        tool_executor(tool_name, arguments), timeout=timeout
                    )
                else:
                    result = await tool_executor(tool_name, arguments)
                return result

            except Exception:
                if attempt == max_attempts - 1:
                    raise

                # Wait before retry
                delay = initial_delay * (backoff_factor**attempt)
                logger.warning(
                    f"Step {step.id} attempt {attempt + 1} failed, retrying in {delay}s"
                )
                await asyncio.sleep(delay)

    async def _execute_condition_step(
        self, step: WorkflowStep, variables: dict[str, Any]
    ) -> bool:
        """Execute a condition step."""
        condition = step.config.get("condition")
        if not condition:
            raise WorkflowExecutionError(f"Condition not specified for step {step.id}")

        result = self._evaluate_condition(condition, variables)
        return result

    async def _execute_parallel_step(
        self,
        step: WorkflowStep,
        tool_executor: Callable,
        variables: dict[str, Any],
        timeout: int | None,
    ) -> list[Any]:
        """Execute a parallel step."""
        sub_steps = step.config.get("steps", [])
        if not sub_steps:
            raise WorkflowExecutionError(
                f"No sub-steps specified for parallel step {step.id}"
            )

        # Create tasks for sub-steps
        tasks = []
        for sub_step_config in sub_steps:
            sub_step = WorkflowStep(
                id=f"{step.id}_sub_{len(tasks)}",
                name=sub_step_config.get("name", "sub_step"),
                step_type=StepType(sub_step_config.get("type", "tool_call")),
                config=sub_step_config.get("config", {}),
                metadata=sub_step_config.get("metadata", {}),
            )
            task = self.execute_step(sub_step, tool_executor, variables, timeout)
            tasks.append(task)

        # Execute sub-steps in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                raise WorkflowExecutionError(f"Parallel sub-step {i} failed: {result}")

        return results

    async def _execute_loop_step(
        self,
        step: WorkflowStep,
        tool_executor: Callable,
        variables: dict[str, Any],
        timeout: int | None,
    ) -> list[Any]:
        """Execute a loop step."""
        loop_config = step.config.get("loop", {})
        items = loop_config.get("items", [])
        max_iterations = loop_config.get("max_iterations", 100)
        continue_on_error = loop_config.get("continue_on_error", False)

        results = []
        for i, item in enumerate(items[:max_iterations]):
            # Set loop variable
            loop_variables = variables.copy()
            loop_variables["loop_item"] = item
            loop_variables["loop_index"] = i

            # Execute loop body
            body_step = WorkflowStep(
                id=f"{step.id}_body_{i}",
                name=f"Loop body {i}",
                step_type=StepType.TOOL_CALL,
                config=step.config.get("body", {}),
            )

            try:
                result = await self.execute_step(
                    body_step, tool_executor, loop_variables, timeout
                )
                if result.status == StepStatus.COMPLETED:
                    results.append(result.result)
                else:
                    raise WorkflowExecutionError(
                        f"Loop body {i} failed: {result.error}"
                    )
            except Exception as e:
                if continue_on_error:
                    logger.warning(f"Loop iteration {i} failed: {e}")
                    continue
                else:
                    raise

        return results

    async def _execute_delay_step(self, step: WorkflowStep) -> None:
        """Execute a delay step."""
        delay_seconds = step.config.get("delay_seconds", 1.0)
        await asyncio.sleep(delay_seconds)

    async def _execute_http_step(
        self, step: WorkflowStep, variables: dict[str, Any], timeout: int | None
    ) -> Any:
        """Execute an HTTP request step."""
        import httpx

        url = step.config.get("url")
        method = step.config.get("method", "GET")
        headers = step.config.get("headers", {})
        data = self._substitute_variables(step.config.get("data", {}), variables)

        client_timeout = timeout or 30.0

        async with httpx.AsyncClient(timeout=client_timeout) as client:
            response = await client.request(method, url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()

    def _evaluate_condition(
        self, condition: dict[str, Any], variables: dict[str, Any]
    ) -> bool:
        """Evaluate a condition."""
        operator = condition.get("operator")
        left_operand = condition.get("left_operand")
        right_operand = condition.get("right_operand")

        # Get actual values
        left_value = self._get_variable_value(left_operand, variables)
        right_value = (
            self._get_variable_value(right_operand, variables)
            if right_operand
            else None
        )

        # Evaluate condition
        if operator == "equals":
            return left_value == right_value
        elif operator == "not_equals":
            return left_value != right_value
        elif operator == "greater_than":
            return left_value > right_value
        elif operator == "less_than":
            return left_value < right_value
        elif operator == "contains":
            return right_value in left_value
        elif operator == "not_contains":
            return right_value not in left_value
        elif operator == "exists":
            return left_value is not None
        elif operator == "not_exists":
            return left_value is None
        else:
            raise WorkflowExecutionError(f"Unsupported condition operator: {operator}")

    def _get_variable_value(self, variable_path: str, variables: dict[str, Any]) -> Any:
        """Get variable value from workflow variables."""
        if not variable_path.startswith("$"):
            return variable_path

        # Remove $ prefix
        path = variable_path[1:]

        # Navigate through variables
        value = variables
        for part in path.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value

    def _substitute_variables(self, data: Any, variables: dict[str, Any]) -> Any:
        """Substitute variables in data structure."""
        if isinstance(data, str):
            if data.startswith("$"):
                return self._get_variable_value(data, variables)
            return data
        elif isinstance(data, dict):
            return {
                k: self._substitute_variables(v, variables) for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._substitute_variables(item, variables) for item in data]
        else:
            return data
