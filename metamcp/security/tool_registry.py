"""
Tool Registry Security

This module provides security and validation for tool registry operations
including developer registration and verification with database persistence.
"""

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..database.connection import get_async_session
from ..database.models import Developer as DeveloperModel
from ..exceptions import ToolRegistryError
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Developer:
    """Developer model."""

    developer_id: str
    username: str
    email: str
    organization: str
    is_verified: bool
    registration_date: datetime
    tools_created: list[str]
    is_active: bool = True


class ToolRegistrySecurity:
    """
    Tool Registry Security for developer registration and verification.

    This class provides database-backed developer management with secure
    registration and verification capabilities.
    """

    def __init__(self):
        """Initialize Tool Registry Security."""
        self._initialized = False
        self._session_factory: sessionmaker | None = None

    async def initialize(self) -> None:
        """Initialize the tool registry security."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Tool Registry Security...")

            # Get session factory
            self._session_factory = get_async_session()

            # Test database connection
            async with self._session_factory() as session:
                # Try to query developers to test connection
                stmt = select(DeveloperModel).limit(1)
                await session.execute(stmt)

            self._initialized = True
            logger.info("Tool Registry Security initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Tool Registry Security: {e}")
            raise ToolRegistryError(
                message=f"Failed to initialize tool registry security: {str(e)}"
            ) from e

    async def register_developer(
        self, username: str, email: str, organization: str
    ) -> str:
        """
        Register a new developer.

        Args:
            username: Developer username
            email: Developer email
            organization: Developer organization

        Returns:
            Developer ID
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            # Generate unique developer ID
            developer_id = str(uuid.uuid4())

            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            verification_expires = datetime.utcnow() + timedelta(days=7)

            # Create database record
            async with self._session_factory() as session:
                developer_model = DeveloperModel(
                    id=developer_id,
                    username=username,
                    email=email,
                    organization=organization,
                    is_verified=False,
                    registration_date=datetime.utcnow(),
                    tools_created=[],
                    is_active=True,
                    verification_token=verification_token,
                    verification_expires=verification_expires,
                )
                session.add(developer_model)
                await session.commit()

            logger.info(f"Registered developer: {developer_id} ({username})")
            return developer_id

        except Exception as e:
            logger.error(f"Failed to register developer: {e}")
            raise ToolRegistryError(
                message=f"Failed to register developer: {str(e)}"
            ) from e

    async def verify_developer(self, developer_id: str) -> bool:
        """
        Verify a developer.

        Args:
            developer_id: Developer ID to verify

        Returns:
            True if developer was verified, False otherwise
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel).where(DeveloperModel.id == developer_id)
                result = await session.execute(stmt)
                developer = result.scalar_one_or_none()

                if not developer:
                    return False

                developer.is_verified = True
                developer.verification_token = None
                developer.verification_expires = None
                await session.commit()

                logger.info(f"Verified developer: {developer_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to verify developer: {e}")
            return False

    async def can_register_tool(self, developer_id: str) -> bool:
        """
        Check if a developer can register tools.

        Args:
            developer_id: Developer ID to check

        Returns:
            True if developer can register tools, False otherwise
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel).where(
                    DeveloperModel.id == developer_id,
                    DeveloperModel.is_verified == True,
                    DeveloperModel.is_active == True,
                )
                result = await session.execute(stmt)
                developer = result.scalar_one_or_none()

                return developer is not None

        except Exception as e:
            logger.error(f"Failed to check developer permissions: {e}")
            return False

    async def can_manage_tool(self, developer_id: str, tool_id: str) -> bool:
        """
        Check if a developer can manage a specific tool.

        Args:
            developer_id: Developer ID to check
            tool_id: Tool ID to check

        Returns:
            True if developer can manage the tool, False otherwise
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel).where(
                    DeveloperModel.id == developer_id,
                    DeveloperModel.is_verified == True,
                    DeveloperModel.is_active == True,
                )
                result = await session.execute(stmt)
                developer = result.scalar_one_or_none()

                if not developer:
                    return False

                # Check if tool is in developer's tools_created list
                return tool_id in developer.tools_created

        except Exception as e:
            logger.error(f"Failed to check tool management permissions: {e}")
            return False

    async def register_tool_creation(self, developer_id: str, tool_id: str) -> bool:
        """
        Register a tool creation by a developer.

        Args:
            developer_id: Developer ID
            tool_id: Tool ID that was created

        Returns:
            True if tool creation was registered, False otherwise
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel).where(DeveloperModel.id == developer_id)
                result = await session.execute(stmt)
                developer = result.scalar_one_or_none()

                if not developer:
                    return False

                # Add tool to developer's tools_created list
                if tool_id not in developer.tools_created:
                    developer.tools_created.append(tool_id)
                    await session.commit()

                logger.info(
                    f"Registered tool creation: {tool_id} by developer: {developer_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to register tool creation: {e}")
            return False

    async def get_developer_info(self, developer_id: str) -> dict[str, Any] | None:
        """
        Get developer information.

        Args:
            developer_id: Developer ID

        Returns:
            Developer information dictionary or None if not found
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel).where(DeveloperModel.id == developer_id)
                result = await session.execute(stmt)
                developer = result.scalar_one_or_none()

                if not developer:
                    return None

                return {
                    "developer_id": developer.id,
                    "username": developer.username,
                    "email": developer.email,
                    "organization": developer.organization,
                    "is_verified": developer.is_verified,
                    "registration_date": developer.registration_date.isoformat(),
                    "tools_created": developer.tools_created,
                    "is_active": developer.is_active,
                }

        except Exception as e:
            logger.error(f"Failed to get developer info: {e}")
            return None

    async def list_developers(
        self, verified_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        List developers.

        Args:
            verified_only: Only return verified developers

        Returns:
            List of developer information
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel)
                if verified_only:
                    stmt = stmt.where(DeveloperModel.is_verified == True)

                result = await session.execute(stmt)
                developers = result.scalars().all()

                developer_list = []
                for developer in developers:
                    developer_list.append(
                        {
                            "developer_id": developer.id,
                            "username": developer.username,
                            "email": developer.email,
                            "organization": developer.organization,
                            "is_verified": developer.is_verified,
                            "registration_date": developer.registration_date.isoformat(),
                            "tools_created": developer.tools_created,
                            "is_active": developer.is_active,
                        }
                    )

                return developer_list

        except Exception as e:
            logger.error(f"Failed to list developers: {e}")
            return []

    async def deactivate_developer(self, developer_id: str) -> bool:
        """
        Deactivate a developer.

        Args:
            developer_id: Developer ID to deactivate

        Returns:
            True if developer was deactivated, False if not found
        """
        if not self._initialized:
            raise ToolRegistryError(message="Tool Registry Security not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(DeveloperModel).where(DeveloperModel.id == developer_id)
                result = await session.execute(stmt)
                developer = result.scalar_one_or_none()

                if not developer:
                    return False

                developer.is_active = False
                await session.commit()

                logger.info(f"Deactivated developer: {developer_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to deactivate developer: {e}")
            return False

    def validate_tool_registration(self, tool_data: dict[str, Any]) -> bool:
        """
        Validate tool registration data.

        Args:
            tool_data: Tool registration data

        Returns:
            True if tool data is valid, False otherwise
        """
        required_fields = ["name", "description", "version", "author"]

        # Check required fields
        for field in required_fields:
            if field not in tool_data or not tool_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate security level
        security_level = tool_data.get("security_level", 0)
        if (
            not isinstance(security_level, int)
            or security_level < 0
            or security_level > 10
        ):
            logger.warning(f"Invalid security level: {security_level}")
            return False

        # Validate version format
        version = tool_data.get("version", "")
        if not self._is_valid_version(version):
            logger.warning(f"Invalid version format: {version}")
            return False

        return True

    def _is_valid_version(self, version: str) -> bool:
        """
        Check if version string is valid.

        Args:
            version: Version string to validate

        Returns:
            True if version is valid, False otherwise
        """
        # Basic semantic versioning check
        parts = version.split(".")
        if len(parts) < 2 or len(parts) > 3:
            return False

        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    async def _load_developers(self) -> None:
        """Load developers from persistent storage."""
        # Developers are now loaded from database on demand
        pass

    async def shutdown(self) -> None:
        """Shutdown the tool registry security."""
        logger.info("Shutting down Tool Registry Security")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the tool registry security is initialized."""
        return self._initialized


# Global instance
_tool_registry_security: ToolRegistrySecurity | None = None


def get_tool_registry_security() -> ToolRegistrySecurity:
    """Get the global tool registry security instance."""
    global _tool_registry_security
    if _tool_registry_security is None:
        _tool_registry_security = ToolRegistrySecurity()
    return _tool_registry_security
