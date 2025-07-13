"""
Policy Engine

This module provides policy-based access control using OPA.
"""

from typing import Any

import httpx

from ..config import PolicyEngineType
from ..config import get_settings
from ..exceptions import PolicyViolationError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class PolicyEngine:
    """
    Policy Engine for access control using OPA.
    
    This class provides policy evaluation and access control
    functionality using Open Policy Agent.
    """

    def __init__(
        self,
        engine_type: PolicyEngineType,
        opa_url: str | None = None
    ):
        """
        Initialize Policy Engine.
        
        Args:
            engine_type: Type of policy engine to use
            opa_url: OPA server URL (for OPA engine type)
        """
        self.engine_type = engine_type
        self.opa_url = opa_url

        # HTTP client for OPA API calls
        self.http_client = httpx.AsyncClient(timeout=10)

        # Simple policy rules (fallback)
        self.policy_rules = {
            "admin": {
                "resources": ["*"],
                "actions": ["*"]
            },
            "user": {
                "resources": ["tool:*"],
                "actions": ["read", "execute"]
            },
            "anonymous": {
                "resources": ["tool:public"],
                "actions": ["read"]
            }
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the policy engine."""
        if self._initialized:
            return

        try:
            logger.info(f"Initializing Policy Engine: {self.engine_type}")

            if self.engine_type == PolicyEngineType.OPA:
                await self._initialize_opa()
            elif self.engine_type == PolicyEngineType.INTERNAL:
                await self._initialize_internal()
            else:
                logger.warning(f"Unsupported policy engine type: {self.engine_type}")
                await self._initialize_internal()

            self._initialized = True
            logger.info("Policy Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Policy Engine: {e}")
            raise PolicyViolationError(
                message=f"Failed to initialize policy engine: {str(e)}",
                error_code="policy_init_failed"
            ) from e

    async def _initialize_opa(self) -> None:
        """Initialize OPA policy engine."""
        if not self.opa_url:
            raise PolicyViolationError(
                message="OPA URL not configured",
                error_code="missing_opa_url"
            )

        try:
            # Test OPA connection
            response = await self.http_client.get(f"{self.opa_url}/health")
            if response.status_code != 200:
                raise PolicyViolationError(
                    message="OPA server not accessible",
                    error_code="opa_unavailable"
                )

            logger.info("OPA policy engine initialized")

        except Exception as e:
            logger.error(f"Failed to initialize OPA: {e}")
            raise PolicyViolationError(
                message=f"Failed to initialize OPA: {str(e)}",
                error_code="opa_init_failed"
            ) from e

    async def _initialize_internal(self) -> None:
        """Initialize internal policy engine."""
        logger.info("Internal policy engine initialized")

    async def check_access(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if user has access to resource.
        
        Args:
            user_id: User ID
            resource: Resource to access
            action: Action to perform
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            if not self._initialized:
                logger.warning("Policy engine not initialized, denying access")
                return False

            if self.engine_type == PolicyEngineType.OPA:
                return await self._check_access_opa(user_id, resource, action)
            else:
                return await self._check_access_internal(user_id, resource, action)

        except Exception as e:
            logger.error(f"Policy check failed: {e}")
            return False

    async def _check_access_opa(self, user_id: str, resource: str, action: str) -> bool:
        """Check access using OPA."""
        try:
            # Prepare query for OPA
            query_data = {
                "input": {
                    "user": user_id,
                    "resource": resource,
                    "action": action
                }
            }

            response = await self.http_client.post(
                f"{self.opa_url}/v1/data/metamcp/allow",
                json=query_data
            )

            if response.status_code != 200:
                logger.error(f"OPA query failed: {response.text}")
                return False

            result = response.json()
            return result.get("result", False)

        except Exception as e:
            logger.error(f"OPA access check failed: {e}")
            return False

    async def _check_access_internal(self, user_id: str, resource: str, action: str) -> bool:
        """Check access using internal policy rules."""
        try:
            # Get user role (simplified)
            user_role = self._get_user_role(user_id)

            # Get policy rules for user role
            rules = self.policy_rules.get(user_role, {})

            # Check if resource is allowed
            allowed_resources = rules.get("resources", [])
            if "*" not in allowed_resources and resource not in allowed_resources:
                return False

            # Check if action is allowed
            allowed_actions = rules.get("actions", [])
            if "*" not in allowed_actions and action not in allowed_actions:
                return False

            return True

        except Exception as e:
            logger.error(f"Internal access check failed: {e}")
            return False

    def _get_user_role(self, user_id: str) -> str:
        """Get user role from user ID."""
        # Simplified role mapping
        if user_id == "admin":
            return "admin"
        elif user_id == "user":
            return "user"
        else:
            return "anonymous"

    async def evaluate_policy(
        self,
        policy_name: str,
        input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Evaluate a policy with input data.
        
        Args:
            policy_name: Name of the policy to evaluate
            input_data: Input data for policy evaluation
            
        Returns:
            Policy evaluation result
        """
        try:
            if not self._initialized:
                raise PolicyViolationError(
                    message="Policy engine not initialized",
                    error_code="policy_not_initialized"
                )

            if self.engine_type == PolicyEngineType.OPA:
                return await self._evaluate_policy_opa(policy_name, input_data)
            else:
                return await self._evaluate_policy_internal(policy_name, input_data)

        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            raise PolicyViolationError(
                message=f"Policy evaluation failed: {str(e)}",
                error_code="policy_evaluation_failed"
            ) from e

    async def evaluate(self, policy_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate a policy (alias for evaluate_policy).
        
        Args:
            policy_name: Name of the policy to evaluate
            input_data: Input data for policy evaluation
            
        Returns:
            Policy evaluation result
        """
        return await self.evaluate_policy(policy_name, input_data)

    async def check_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            if not self._initialized:
                logger.warning("Policy engine not initialized, denying permission")
                return False

            # Get user role
            user_role = self._get_user_role(user_id)

            # Get policy rules for user role
            rules = self.policy_rules.get(user_role, {})

            # Check if permission is allowed
            allowed_actions = rules.get("actions", [])
            return "*" in allowed_actions or permission in allowed_actions

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    async def _evaluate_policy_opa(self, policy_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate policy using OPA."""
        try:
            query_data = {
                "input": input_data
            }

            response = await self.http_client.post(
                f"{self.opa_url}/v1/data/{policy_name}",
                json=query_data
            )

            if response.status_code != 200:
                raise PolicyViolationError(
                    message=f"OPA policy evaluation failed: {response.text}",
                    error_code="opa_evaluation_failed"
                )

            return response.json()

        except Exception as e:
            logger.error(f"OPA policy evaluation failed: {e}")
            raise PolicyViolationError(
                message=f"OPA policy evaluation failed: {str(e)}",
                error_code="opa_evaluation_failed"
            ) from e

    async def _evaluate_policy_internal(self, policy_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate policy using internal rules."""
        # Simplified internal policy evaluation
        return {
            "result": True,
            "reason": "Internal policy evaluation",
            "policy": policy_name
        }

    async def shutdown(self) -> None:
        """Shutdown the policy engine."""
        if not self._initialized:
            return

        logger.info("Shutting down Policy Engine...")

        # Close HTTP client
        await self.http_client.aclose()

        self._initialized = False
        logger.info("Policy Engine shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized
