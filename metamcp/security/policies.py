"""
Policy Engine

This module provides policy-based access control using OPA with predefined policies,
versioning, and advanced security features.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx

from ..config import PolicyEngineType, get_settings
from ..exceptions import PolicyViolationError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class PolicyVersion:
    """Policy version information."""

    version: str
    content: str
    description: str
    created_at: datetime
    created_by: str
    is_active: bool = True
    is_deprecated: bool = False


@dataclass
class PolicyRule:
    """Policy rule definition."""

    name: str
    description: str
    resource_pattern: str
    action_pattern: str
    conditions: dict[str, Any]
    priority: int = 0


class PolicyEngine:
    """
    Policy Engine for access control using OPA with advanced features.

    This class provides policy evaluation and access control functionality
    using Open Policy Agent with predefined policies, versioning, and
    advanced security features.
    """

    def __init__(self, engine_type: PolicyEngineType, opa_url: str | None = None):
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

        # Policy versions storage
        self.policy_versions: dict[str, list[PolicyVersion]] = {}

        # Active policies cache
        self.active_policies: dict[str, PolicyVersion] = {}

        # Policy rules cache
        self.policy_rules: dict[str, list[PolicyRule]] = {}

        # Simple policy rules (fallback)
        self.fallback_rules = {
            "admin": {"resources": ["*"], "actions": ["*"]},
            "user": {"resources": ["tool:*"], "actions": ["read", "execute"]},
            "anonymous": {"resources": ["tool:public"], "actions": ["read"]},
        }

        # Rate limiting cache
        self.rate_limit_cache: dict[str, dict[str, Any]] = {}

        # IP whitelist/blacklist
        self.ip_whitelist: list[str] = []
        self.ip_blacklist: list[str] = []

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the policy engine."""
        if self._initialized:
            return

        try:
            logger.info(f"Initializing Policy Engine: {self.engine_type}")

            # Load predefined policies
            await self._load_predefined_policies()

            # Load policy versions
            await self._load_policy_versions()

            # Initialize engine type
            if self.engine_type == PolicyEngineType.OPA:
                await self._initialize_opa()
            elif self.engine_type == PolicyEngineType.INTERNAL:
                await self._initialize_internal()
            else:
                logger.warning(f"Unsupported policy engine type: {self.engine_type}")
                await self._initialize_internal()

            # Load IP lists
            await self._load_ip_lists()

            self._initialized = True
            logger.info("Policy Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Policy Engine: {e}")
            raise PolicyViolationError(
                message=f"Failed to initialize policy engine: {str(e)}",
                error_code="policy_init_failed",
            ) from e

    async def _load_predefined_policies(self) -> None:
        """Load predefined policies."""
        try:
            # Tool access policies
            self._add_predefined_policy(
                "tool_access",
                "1.0.0",
                """
                package metamcp.tool_access

                default allow = false

                allow {
                    input.action == "read"
                    input.resource = startswith("tool:")
                    input.user.role == "user"
                }

                allow {
                    input.action == "execute"
                    input.resource = startswith("tool:")
                    input.user.role == "user"
                    input.user.permissions[_] == "tool_execute"
                }

                allow {
                    input.action == "manage"
                    input.resource = startswith("tool:")
                    input.user.role == "admin"
                }
                """,
                "Tool access control policy",
            )

            # API rate limiting policy
            self._add_predefined_policy(
                "rate_limiting",
                "1.0.0",
                """
                package metamcp.rate_limiting

                default allow = true

                allow = false {
                    input.rate_limit_exceeded == true
                }

                rate_limit_exceeded {
                    input.request_count > input.limit
                    input.window_start < time.now_ns()
                }
                """,
                "API rate limiting policy",
            )

            # Resource quota policy
            self._add_predefined_policy(
                "resource_quota",
                "1.0.0",
                """
                package metamcp.resource_quota

                default allow = true

                allow = false {
                    input.resource_usage > input.quota_limit
                }

                quota_exceeded {
                    input.resource_usage > input.quota_limit
                }
                """,
                "Resource quota enforcement policy",
            )

            # IP filtering policy
            self._add_predefined_policy(
                "ip_filtering",
                "1.0.0",
                """
                package metamcp.ip_filtering

                default allow = true

                allow = false {
                    input.ip in data.blacklisted_ips
                }

                allow = false {
                    not input.ip in data.whitelisted_ips
                    count(data.whitelisted_ips) > 0
                }
                """,
                "IP filtering policy",
            )

            # Data access policy
            self._add_predefined_policy(
                "data_access",
                "1.0.0",
                """
                package metamcp.data_access

                default allow = false

                allow {
                    input.action == "read"
                    input.resource = startswith("data:public:")
                }

                allow {
                    input.action == "read"
                    input.resource = startswith("data:user:")
                    input.user.id == input.resource_user_id
                }

                allow {
                    input.action == "write"
                    input.resource = startswith("data:user:")
                    input.user.id == input.resource_user_id
                    input.user.permissions[_] == "data_write"
                }

                allow {
                    input.action == "delete"
                    input.resource = startswith("data:user:")
                    input.user.id == input.resource_user_id
                    input.user.permissions[_] == "data_delete"
                }
                """,
                "Data access control policy",
            )

            logger.info("Loaded predefined policies")

        except Exception as e:
            logger.error(f"Failed to load predefined policies: {e}")
            raise PolicyViolationError(
                message=f"Failed to load predefined policies: {str(e)}",
                error_code="policy_load_failed",
            ) from e

    def _add_predefined_policy(
        self, name: str, version: str, content: str, description: str
    ) -> None:
        """Add a predefined policy."""
        if name not in self.policy_versions:
            self.policy_versions[name] = []

        policy_version = PolicyVersion(
            version=version,
            content=content,
            description=description,
            created_at=datetime.utcnow(),
            created_by="system",
        )

        self.policy_versions[name].append(policy_version)
        self.active_policies[name] = policy_version

    async def _load_policy_versions(self) -> None:
        """Load policy versions from storage."""
        # In a real implementation, this would load from database
        # For now, we use the predefined policies
        pass

    async def _load_ip_lists(self) -> None:
        """Load IP whitelist and blacklist."""
        # In a real implementation, this would load from database or file
        # For now, we use empty lists
        self.ip_whitelist = []
        self.ip_blacklist = []

    async def _initialize_opa(self) -> None:
        """Initialize OPA policy engine."""
        if not self.opa_url:
            raise PolicyViolationError(
                message="OPA URL not configured", error_code="missing_opa_url"
            )

        try:
            # Test OPA connection
            response = await self.http_client.get(f"{self.opa_url}/health")
            if response.status_code != 200:
                raise PolicyViolationError(
                    message="OPA server not accessible", error_code="opa_unavailable"
                )

            # Upload predefined policies to OPA
            await self._upload_policies_to_opa()

            logger.info("OPA policy engine initialized")

        except Exception as e:
            logger.error(f"Failed to initialize OPA: {e}")
            raise PolicyViolationError(
                message=f"Failed to initialize OPA: {str(e)}",
                error_code="opa_init_failed",
            ) from e

    async def _upload_policies_to_opa(self) -> None:
        """Upload policies to OPA server."""
        try:
            for policy_name, policy_version in self.active_policies.items():
                # Create OPA policy document
                policy_doc = {
                    "id": f"{policy_name}-{policy_version.version}",
                    "modules": {f"{policy_name}.rego": policy_version.content},
                }

                # Upload to OPA
                response = await self.http_client.put(
                    f"{self.opa_url}/v1/policies/{policy_name}", json=policy_doc
                )

                if response.status_code not in [200, 201]:
                    logger.warning(
                        f"Failed to upload policy {policy_name}: {response.text}"
                    )

            logger.info("Uploaded policies to OPA")

        except Exception as e:
            logger.error(f"Failed to upload policies to OPA: {e}")

    async def _initialize_internal(self) -> None:
        """Initialize internal policy engine."""
        logger.info("Internal policy engine initialized")

    async def check_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if user has access to resource with advanced context.

        Args:
            user_id: User ID
            resource: Resource to access
            action: Action to perform
            context: Additional context (IP, time, etc.)

        Returns:
            True if access is allowed, False otherwise
        """
        try:
            if not self._initialized:
                logger.warning("Policy engine not initialized, denying access")
                return False

            # Check IP filtering first
            if context and "ip" in context:
                if not await self._check_ip_access(context["ip"]):
                    logger.warning(f"IP access denied: {context['ip']}")
                    return False

            # Check rate limiting
            if context and "rate_limit_key" in context:
                if not await self._check_rate_limit(
                    context["rate_limit_key"], context.get("limit", 100)
                ):
                    logger.warning(
                        f"Rate limit exceeded for: {context['rate_limit_key']}"
                    )
                    return False

            # Check resource quota
            if context and "quota_key" in context:
                if not await self._check_resource_quota(
                    context["quota_key"],
                    context.get("usage", 0),
                    context.get("limit", 1000),
                ):
                    logger.warning(
                        f"Resource quota exceeded for: {context['quota_key']}"
                    )
                    return False

            # Check main access policy
            if self.engine_type == PolicyEngineType.OPA:
                return await self._check_access_opa(user_id, resource, action, context)
            else:
                return await self._check_access_internal(
                    user_id, resource, action, context
                )

        except Exception as e:
            logger.error(f"Policy check failed: {e}")
            return False

    async def _check_ip_access(self, ip: str) -> bool:
        """Check IP access against whitelist/blacklist."""
        # Check blacklist first
        if ip in self.ip_blacklist:
            return False

        # If whitelist is not empty, check whitelist
        if self.ip_whitelist and ip not in self.ip_whitelist:
            return False

        return True

    async def _check_rate_limit(self, key: str, limit: int) -> bool:
        """Check rate limiting."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)  # 1-minute window

        if key not in self.rate_limit_cache:
            self.rate_limit_cache[key] = {"count": 0, "window_start": now}

        cache_entry = self.rate_limit_cache[key]

        # Reset window if expired
        if cache_entry["window_start"] < window_start:
            cache_entry["count"] = 0
            cache_entry["window_start"] = now

        # Check limit
        if cache_entry["count"] >= limit:
            return False

        # Increment count
        cache_entry["count"] += 1
        return True

    async def _check_resource_quota(self, key: str, usage: int, limit: int) -> bool:
        """Check resource quota."""
        return usage <= limit

    async def _check_access_opa(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check access using OPA."""
        try:
            # Prepare input data
            input_data = {
                "user": {"id": user_id, "role": self._get_user_role(user_id)},
                "resource": resource,
                "action": action,
            }

            if context:
                input_data.update(context)

            # Determine which policy to use based on resource
            policy_name = self._get_policy_name_for_resource(resource)

            if policy_name not in self.active_policies:
                logger.warning(f"No policy found for resource: {resource}")
                return False

            # Query OPA
            query_data = {"input": input_data}
            response = await self.http_client.post(
                f"{self.opa_url}/v1/data/{policy_name}/allow", json=query_data
            )

            if response.status_code != 200:
                logger.error(f"OPA query failed: {response.text}")
                return False

            result = response.json()
            return result.get("result", False)

        except Exception as e:
            logger.error(f"OPA access check failed: {e}")
            return False

    def _get_policy_name_for_resource(self, resource: str) -> str:
        """Get policy name for resource."""
        if resource.startswith("tool:"):
            return "tool_access"
        elif resource.startswith("data:"):
            return "data_access"
        elif resource.startswith("api:"):
            return "rate_limiting"
        else:
            return "tool_access"  # Default

    async def _check_access_internal(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check access using internal policy rules."""
        try:
            # Get user role
            user_role = self._get_user_role(user_id)

            # Get policy rules for user role
            rules = self.fallback_rules.get(user_role, {})

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
        # Simplified role mapping - in real implementation, this would query the database
        if user_id == "admin":
            return "admin"
        elif user_id == "user":
            return "user"
        else:
            return "anonymous"

    async def evaluate_policy(
        self, policy_name: str, input_data: dict[str, Any]
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
                    error_code="policy_not_initialized",
                )

            if policy_name not in self.active_policies:
                raise PolicyViolationError(
                    message=f"Policy not found: {policy_name}",
                    error_code="policy_not_found",
                )

            if self.engine_type == PolicyEngineType.OPA:
                return await self._evaluate_policy_opa(policy_name, input_data)
            else:
                return await self._evaluate_policy_internal(policy_name, input_data)

        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            raise PolicyViolationError(
                message=f"Policy evaluation failed: {str(e)}",
                error_code="policy_evaluation_failed",
            ) from e

    async def evaluate(
        self, policy_name: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Alias for evaluate_policy for backward compatibility.

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
            # This is a simplified permission check
            # In a real implementation, this would query user permissions from database
            user_role = self._get_user_role(user_id)

            if user_role == "admin":
                return True
            elif user_role == "user":
                return permission in [
                    "tool_read",
                    "tool_execute",
                    "data_read",
                    "data_write",
                ]
            else:
                return permission in ["tool_read"]

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    async def _evaluate_policy_opa(
        self, policy_name: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate policy using OPA."""
        try:
            query_data = {"input": input_data}
            response = await self.http_client.post(
                f"{self.opa_url}/v1/data/{policy_name}", json=query_data
            )

            if response.status_code != 200:
                raise PolicyViolationError(
                    message=f"OPA evaluation failed: {response.text}",
                    error_code="opa_evaluation_failed",
                )

            return response.json()

        except Exception as e:
            logger.error(f"OPA policy evaluation failed: {e}")
            raise PolicyViolationError(
                message=f"OPA policy evaluation failed: {str(e)}",
                error_code="opa_evaluation_failed",
            ) from e

    async def _evaluate_policy_internal(
        self, policy_name: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate policy using internal engine."""
        # Simplified internal policy evaluation
        return {"result": True, "reason": "Internal policy evaluation"}

    # Policy Management Methods

    async def create_policy(
        self, name: str, content: str, description: str, created_by: str
    ) -> str:
        """
        Create a new policy.

        Args:
            name: Policy name
            content: Policy content (Rego for OPA)
            description: Policy description
            created_by: User who created the policy

        Returns:
            Policy version ID
        """
        try:
            version_id = str(uuid.uuid4())

            if name not in self.policy_versions:
                self.policy_versions[name] = []

            policy_version = PolicyVersion(
                version=version_id,
                content=content,
                description=description,
                created_at=datetime.utcnow(),
                created_by=created_by,
            )

            self.policy_versions[name].append(policy_version)
            self.active_policies[name] = policy_version

            # Upload to OPA if using OPA engine
            if self.engine_type == PolicyEngineType.OPA:
                await self._upload_policies_to_opa()

            logger.info(f"Created policy: {name} (version: {version_id})")
            return version_id

        except Exception as e:
            logger.error(f"Failed to create policy: {e}")
            raise PolicyViolationError(
                message=f"Failed to create policy: {str(e)}",
                error_code="policy_creation_failed",
            ) from e

    async def update_policy(
        self, name: str, content: str, description: str, updated_by: str
    ) -> str:
        """
        Update an existing policy.

        Args:
            name: Policy name
            content: New policy content
            description: New policy description
            updated_by: User who updated the policy

        Returns:
            New policy version ID
        """
        try:
            if name not in self.policy_versions:
                raise PolicyViolationError(
                    message=f"Policy not found: {name}", error_code="policy_not_found"
                )

            # Create new version
            version_id = str(uuid.uuid4())
            policy_version = PolicyVersion(
                version=version_id,
                content=content,
                description=description,
                created_at=datetime.utcnow(),
                created_by=updated_by,
            )

            # Deprecate old version
            if self.policy_versions[name]:
                self.policy_versions[name][-1].is_deprecated = True

            self.policy_versions[name].append(policy_version)
            self.active_policies[name] = policy_version

            # Upload to OPA if using OPA engine
            if self.engine_type == PolicyEngineType.OPA:
                await self._upload_policies_to_opa()

            logger.info(f"Updated policy: {name} (version: {version_id})")
            return version_id

        except Exception as e:
            logger.error(f"Failed to update policy: {e}")
            raise PolicyViolationError(
                message=f"Failed to update policy: {str(e)}",
                error_code="policy_update_failed",
            ) from e

    async def get_policy_versions(self, name: str) -> list[PolicyVersion]:
        """
        Get all versions of a policy.

        Args:
            name: Policy name

        Returns:
            List of policy versions
        """
        return self.policy_versions.get(name, [])

    async def activate_policy_version(self, name: str, version: str) -> bool:
        """
        Activate a specific policy version.

        Args:
            name: Policy name
            version: Policy version

        Returns:
            True if activated successfully
        """
        try:
            if name not in self.policy_versions:
                return False

            for policy_version in self.policy_versions[name]:
                if policy_version.version == version:
                    self.active_policies[name] = policy_version

                    # Upload to OPA if using OPA engine
                    if self.engine_type == PolicyEngineType.OPA:
                        await self._upload_policies_to_opa()

                    logger.info(f"Activated policy: {name} (version: {version})")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to activate policy version: {e}")
            return False

    async def add_ip_to_whitelist(self, ip: str) -> bool:
        """Add IP to whitelist."""
        try:
            if ip not in self.ip_whitelist:
                self.ip_whitelist.append(ip)
                logger.info(f"Added IP to whitelist: {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to add IP to whitelist: {e}")
            return False

    async def add_ip_to_blacklist(self, ip: str) -> bool:
        """Add IP to blacklist."""
        try:
            if ip not in self.ip_blacklist:
                self.ip_blacklist.append(ip)
                logger.info(f"Added IP to blacklist: {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to add IP to blacklist: {e}")
            return False

    async def remove_ip_from_whitelist(self, ip: str) -> bool:
        """Remove IP from whitelist."""
        try:
            if ip in self.ip_whitelist:
                self.ip_whitelist.remove(ip)
                logger.info(f"Removed IP from whitelist: {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove IP from whitelist: {e}")
            return False

    async def remove_ip_from_blacklist(self, ip: str) -> bool:
        """Remove IP from blacklist."""
        try:
            if ip in self.ip_blacklist:
                self.ip_blacklist.remove(ip)
                logger.info(f"Removed IP from blacklist: {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove IP from blacklist: {e}")
            return False

    async def get_ip_lists(self) -> dict[str, list[str]]:
        """Get current IP whitelist and blacklist."""
        return {
            "whitelist": self.ip_whitelist.copy(),
            "blacklist": self.ip_blacklist.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the policy engine."""
        try:
            await self.http_client.aclose()
            logger.info("Policy Engine shutdown complete")
        except Exception as e:
            logger.error(f"Error during policy engine shutdown: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if the policy engine is initialized."""
        return self._initialized
