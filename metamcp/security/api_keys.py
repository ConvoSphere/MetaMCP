"""
API Key Management System

This module provides API key generation, validation, and management
for service-to-service authentication.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass

from ..config import get_settings
from ..exceptions import AuthenticationError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class APIKey:
    """API Key model."""
    key_id: str
    key_hash: str
    name: str
    owner: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool = True


class APIKeyManager:
    """
    API Key Manager for service-to-service authentication.
    
    Handles API key generation, validation, and management.
    """

    def __init__(self):
        """Initialize API Key Manager."""
        self.keys: Dict[str, APIKey] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the API key manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing API Key Manager...")
            
            # Load existing keys from database/storage
            await self._load_keys()
            
            self._initialized = True
            logger.info("API Key Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API Key Manager: {e}")
            raise AuthenticationError(
                message=f"Failed to initialize API key manager: {str(e)}"
            )

    def generate_api_key(self, name: str, owner: str, permissions: List[str], 
                        expires_in_days: Optional[int] = None) -> str:
        """
        Generate a new API key.
        
        Args:
            name: Human-readable name for the key
            owner: Owner of the key (service/user)
            permissions: List of permissions granted to this key
            expires_in_days: Days until key expires (None for no expiration)
            
        Returns:
            The generated API key (only returned once)
        """
        # Generate unique key ID
        key_id = f"key_{secrets.token_urlsafe(16)}"
        
        # Generate the actual API key
        api_key = f"mcp_{secrets.token_urlsafe(32)}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key record
        key_record = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            owner=owner,
            permissions=permissions,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_used=None,
            is_active=True
        )
        
        # Store the key record
        self.keys[key_id] = key_record
        
        logger.info(f"Generated API key '{name}' for {owner}")
        
        # Return the actual key (only time it's available)
        return api_key

    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            APIKey object if valid, None otherwise
        """
        if not api_key or not api_key.startswith("mcp_"):
            return None
        
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find matching key
        for key_record in self.keys.values():
            if (key_record.key_hash == key_hash and 
                key_record.is_active and
                (key_record.expires_at is None or key_record.expires_at > datetime.utcnow())):
                
                # Update last used timestamp
                key_record.last_used = datetime.utcnow()
                return key_record
        
        return None

    def check_permission(self, api_key: str, permission: str) -> bool:
        """
        Check if an API key has a specific permission.
        
        Args:
            api_key: The API key to check
            permission: The permission to check
            
        Returns:
            True if key has permission, False otherwise
        """
        key_record = self.validate_api_key(api_key)
        if not key_record:
            return False
        
        return permission in key_record.permissions

    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: The ID of the key to revoke
            
        Returns:
            True if key was revoked, False if not found
        """
        if key_id in self.keys:
            self.keys[key_id].is_active = False
            logger.info(f"Revoked API key: {key_id}")
            return True
        return False

    def list_api_keys(self, owner: Optional[str] = None) -> List[Dict]:
        """
        List API keys.
        
        Args:
            owner: Filter by owner (optional)
            
        Returns:
            List of API key information (without actual keys)
        """
        keys = []
        for key_record in self.keys.values():
            if owner and key_record.owner != owner:
                continue
                
            keys.append({
                "key_id": key_record.key_id,
                "name": key_record.name,
                "owner": key_record.owner,
                "permissions": key_record.permissions,
                "created_at": key_record.created_at.isoformat(),
                "expires_at": key_record.expires_at.isoformat() if key_record.expires_at else None,
                "last_used": key_record.last_used.isoformat() if key_record.last_used else None,
                "is_active": key_record.is_active
            })
        
        return keys

    async def _load_keys(self) -> None:
        """Load API keys from persistent storage."""
        # TODO: Implement database storage for API keys
        # For now, keys are stored in memory
        pass

    async def shutdown(self) -> None:
        """Shutdown the API key manager."""
        logger.info("Shutting down API Key Manager")
        # TODO: Save keys to persistent storage
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the API key manager is initialized."""
        return self._initialized


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager