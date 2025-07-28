"""
Tool Registry Security

This module provides security controls for tool registration and management,
ensuring only registered developers can manage tools.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ..config import get_settings
from ..exceptions import AuthorizationError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class Developer:
    """Developer model."""
    developer_id: str
    username: str
    email: str
    organization: str
    is_verified: bool
    registration_date: datetime
    tools_created: List[str]
    is_active: bool = True


class ToolRegistrySecurity:
    """
    Tool Registry Security Manager.
    
    Controls access to tool registration and management operations.
    """

    def __init__(self):
        """Initialize Tool Registry Security."""
        self.developers: Dict[str, Developer] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the tool registry security."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Tool Registry Security...")
            
            # Load registered developers
            await self._load_developers()
            
            self._initialized = True
            logger.info("Tool Registry Security initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Tool Registry Security: {e}")
            raise AuthorizationError(
                message=f"Failed to initialize tool registry security: {str(e)}"
            )

    def register_developer(self, username: str, email: str, organization: str) -> str:
        """
        Register a new developer.
        
        Args:
            username: Developer username
            email: Developer email
            organization: Developer organization
            
        Returns:
            Developer ID
        """
        # Check if developer already exists
        for dev in self.developers.values():
            if dev.email == email or dev.username == username:
                raise AuthorizationError(
                    message="Developer already registered with this email or username"
                )
        
        # Generate developer ID
        developer_id = f"dev_{username}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Create developer record
        developer = Developer(
            developer_id=developer_id,
            username=username,
            email=email,
            organization=organization,
            is_verified=False,  # Requires manual verification
            registration_date=datetime.utcnow(),
            tools_created=[],
            is_active=True
        )
        
        self.developers[developer_id] = developer
        
        logger.info(f"Registered developer: {username} ({organization})")
        
        return developer_id

    def verify_developer(self, developer_id: str) -> bool:
        """
        Verify a developer (admin operation).
        
        Args:
            developer_id: Developer ID to verify
            
        Returns:
            True if developer was verified, False if not found
        """
        if developer_id in self.developers:
            self.developers[developer_id].is_verified = True
            logger.info(f"Verified developer: {developer_id}")
            return True
        return False

    def can_register_tool(self, developer_id: str) -> bool:
        """
        Check if a developer can register tools.
        
        Args:
            developer_id: Developer ID to check
            
        Returns:
            True if developer can register tools, False otherwise
        """
        if developer_id not in self.developers:
            return False
        
        developer = self.developers[developer_id]
        return developer.is_active and developer.is_verified

    def can_manage_tool(self, developer_id: str, tool_id: str) -> bool:
        """
        Check if a developer can manage a specific tool.
        
        Args:
            developer_id: Developer ID to check
            tool_id: Tool ID to check
            
        Returns:
            True if developer can manage the tool, False otherwise
        """
        if not self.can_register_tool(developer_id):
            return False
        
        developer = self.developers[developer_id]
        return tool_id in developer.tools_created

    def register_tool_creation(self, developer_id: str, tool_id: str) -> bool:
        """
        Register that a developer created a tool.
        
        Args:
            developer_id: Developer ID
            tool_id: Tool ID that was created
            
        Returns:
            True if registration was successful, False otherwise
        """
        if developer_id in self.developers:
            if tool_id not in self.developers[developer_id].tools_created:
                self.developers[developer_id].tools_created.append(tool_id)
                logger.info(f"Registered tool creation: {tool_id} by {developer_id}")
            return True
        return False

    def get_developer_info(self, developer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get developer information.
        
        Args:
            developer_id: Developer ID
            
        Returns:
            Developer information or None if not found
        """
        if developer_id not in self.developers:
            return None
        
        developer = self.developers[developer_id]
        return {
            "developer_id": developer.developer_id,
            "username": developer.username,
            "email": developer.email,
            "organization": developer.organization,
            "is_verified": developer.is_verified,
            "registration_date": developer.registration_date.isoformat(),
            "tools_created": developer.tools_created,
            "is_active": developer.is_active
        }

    def list_developers(self, verified_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all developers.
        
        Args:
            verified_only: Only return verified developers
            
        Returns:
            List of developer information
        """
        developers = []
        for developer in self.developers.values():
            if verified_only and not developer.is_verified:
                continue
                
            developers.append(self.get_developer_info(developer.developer_id))
        
        return developers

    def deactivate_developer(self, developer_id: str) -> bool:
        """
        Deactivate a developer.
        
        Args:
            developer_id: Developer ID to deactivate
            
        Returns:
            True if developer was deactivated, False if not found
        """
        if developer_id in self.developers:
            self.developers[developer_id].is_active = False
            logger.info(f"Deactivated developer: {developer_id}")
            return True
        return False

    def validate_tool_registration(self, tool_data: Dict[str, Any]) -> bool:
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
        if not isinstance(security_level, int) or security_level < 0 or security_level > 10:
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
        # TODO: Implement database storage for developers
        # For now, developers are stored in memory
        pass

    async def shutdown(self) -> None:
        """Shutdown the tool registry security."""
        logger.info("Shutting down Tool Registry Security")
        # TODO: Save developers to persistent storage
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the tool registry security is initialized."""
        return self._initialized


# Global instance
_tool_registry_security: Optional[ToolRegistrySecurity] = None


def get_tool_registry_security() -> ToolRegistrySecurity:
    """Get the global tool registry security instance."""
    global _tool_registry_security
    if _tool_registry_security is None:
        _tool_registry_security = ToolRegistrySecurity()
    return _tool_registry_security