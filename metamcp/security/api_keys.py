"""
API Key Management

This module provides API key management functionality including generation,
validation, and storage with database persistence.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from ..database.connection import get_async_session
from ..database.models import APIKey as APIKeyModel
from ..exceptions import APIKeyError
from ..utils.logging import get_logger

logger = get_logger(__name__)


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
    API Key Manager for generating, validating, and managing API keys.
    
    This class provides database-backed API key management with secure
    storage and validation capabilities.
    """

    def __init__(self):
        """Initialize API Key Manager."""
        self._initialized = False
        self._session_factory: Optional[sessionmaker] = None

    async def initialize(self) -> None:
        """Initialize the API key manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing API Key Manager...")
            
            # Get session factory
            self._session_factory = get_async_session()
            
            # Test database connection
            async with self._session_factory() as session:
                # Try to query API keys to test connection
                stmt = select(APIKeyModel).limit(1)
                await session.execute(stmt)
            
            self._initialized = True
            logger.info("API Key Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API Key Manager: {e}")
            raise APIKeyError(
                message=f"Failed to initialize API key manager: {str(e)}"
            ) from e

    def generate_api_key(self, name: str, owner: str, permissions: List[str], 
                        expires_in_days: Optional[int] = None) -> str:
        """
        Generate a new API key.
        
        Args:
            name: Name for the API key
            owner: Owner of the API key
            permissions: List of permissions for the key
            expires_in_days: Days until key expires (optional)
            
        Returns:
            The generated API key string
        """
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")

        try:
            # Generate unique key ID
            key_id = str(uuid.uuid4())
            
            # Generate secure random key
            api_key = f"mcp_{secrets.token_urlsafe(32)}"
            
            # Hash the key for storage
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create database record
            asyncio.create_task(self._save_api_key_to_db(
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                owner=owner,
                permissions=permissions,
                expires_at=expires_at
            ))
            
            logger.info(f"Generated API key: {key_id} for owner: {owner}")
            return api_key

        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise APIKeyError(
                message=f"Failed to generate API key: {str(e)}"
            ) from e

    async def _save_api_key_to_db(self, key_id: str, key_hash: str, name: str, 
                                 owner: str, permissions: List[str], 
                                 expires_at: Optional[datetime]) -> None:
        """Save API key to database."""
        try:
            async with self._session_factory() as session:
                api_key_model = APIKeyModel(
                    id=key_id,
                    key_hash=key_hash,
                    name=name,
                    user_id=owner,
                    permissions=permissions,
                    created_at=datetime.utcnow(),
                    expires_at=expires_at,
                    is_active=True
                )
                session.add(api_key_model)
                await session.commit()
                logger.debug(f"Saved API key to database: {key_id}")

        except Exception as e:
            logger.error(f"Failed to save API key to database: {e}")
            raise APIKeyError(
                message=f"Failed to save API key to database: {str(e)}"
            ) from e

    async def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            APIKey object if valid, None otherwise
        """
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")

        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Query database for the key
            async with self._session_factory() as session:
                stmt = select(APIKeyModel).where(
                    APIKeyModel.key_hash == key_hash,
                    APIKeyModel.is_active == True
                )
                result = await session.execute(stmt)
                key_record = result.scalar_one_or_none()
                
                if not key_record:
                    return None
                
                # Check expiration
                if (key_record.expires_at and 
                    key_record.expires_at < datetime.utcnow()):
                    logger.warning(f"API key expired: {key_record.id}")
                    return None
                
                # Update last used timestamp
                key_record.last_used = datetime.utcnow()
                await session.commit()
                
                # Return APIKey object
                return APIKey(
                    key_id=key_record.id,
                    key_hash=key_record.key_hash,
                    name=key_record.name,
                    owner=key_record.user_id,
                    permissions=key_record.permissions,
                    created_at=key_record.created_at,
                    expires_at=key_record.expires_at,
                    last_used=key_record.last_used,
                    is_active=key_record.is_active
                )

        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
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
        key_record = asyncio.run(self.validate_api_key(api_key))
        if not key_record:
            return False
        
        return permission in key_record.permissions

    async def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: The ID of the key to revoke
            
        Returns:
            True if key was revoked, False if not found
        """
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(APIKeyModel).where(APIKeyModel.id == key_id)
                result = await session.execute(stmt)
                key_record = result.scalar_one_or_none()
                
                if not key_record:
                    return False
                
                key_record.is_active = False
                await session.commit()
                
                logger.info(f"Revoked API key: {key_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

    async def list_api_keys(self, owner: Optional[str] = None) -> List[Dict]:
        """
        List API keys.
        
        Args:
            owner: Filter by owner (optional)
            
        Returns:
            List of API key information (without actual keys)
        """
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(APIKeyModel)
                if owner:
                    stmt = stmt.where(APIKeyModel.user_id == owner)
                
                result = await session.execute(stmt)
                key_records = result.scalars().all()
                
                keys = []
                for key_record in key_records:
                    keys.append({
                        "key_id": key_record.id,
                        "name": key_record.name,
                        "owner": key_record.user_id,
                        "permissions": key_record.permissions,
                        "created_at": key_record.created_at.isoformat(),
                        "expires_at": key_record.expires_at.isoformat() if key_record.expires_at else None,
                        "last_used": key_record.last_used.isoformat() if key_record.last_used else None,
                        "is_active": key_record.is_active
                    })
                
                return keys

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    async def _load_keys(self) -> None:
        """Load API keys from persistent storage."""
        # Keys are now loaded from database on demand
        pass

    async def shutdown(self) -> None:
        """Shutdown the API key manager."""
        logger.info("Shutting down API Key Manager")
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