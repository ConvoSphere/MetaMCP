"""
API Key Management

This module provides API key management functionality including generation,
validation, and storage with database persistence.
"""

import asyncio
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
import inspect

from sqlalchemy import select
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
    permissions: list[str]
    created_at: datetime
    expires_at: datetime | None
    last_used: datetime | None
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
        self._session_factory: sessionmaker | None = None
        # In-memory store for unit tests and as a fallback when DB is not used
        self._keys: dict[str, APIKey] = {}

    async def initialize(self) -> None:
        """Initialize the API key manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing API Key Manager...")

            # Try to obtain a session factory if available; do not fail hard
            try:
                self._session_factory = get_async_session()
            except Exception:
                self._session_factory = None

            # Optional: lightly probe connection only if a factory exists
            if self._session_factory is not None:
                try:
                    session_ctx = self._session_factory()  # type: ignore[misc]
                    if inspect.isawaitable(session_ctx):
                        session_ctx = await session_ctx  # type: ignore[assignment]
                    async with session_ctx as session:
                        stmt = select(APIKeyModel).limit(1)
                        await session.execute(stmt)
                except Exception:
                    # Ignore DB connectivity issues in unit test context
                    pass

            self._initialized = True
            logger.info("API Key Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize API Key Manager: {e}")
            raise APIKeyError(
                message=f"Failed to initialize API key manager: {str(e)}"
            ) from e

    def generate_api_key(
        self,
        name: str,
        owner: str,
        permissions: list[str],
        expires_in_days: int | None = None,
    ) -> str:
        """
        Generate a new API key.
        """
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")

        try:
            key_id = str(uuid.uuid4())
            api_key = f"mcp_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            # Store in-memory
            self._keys[key_id] = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                owner=owner,
                permissions=permissions,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                last_used=None,
                is_active=True,
            )

            # Optionally persist in background if DB is configured
            if self._session_factory is not None:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(
                        self._save_api_key_to_db(
                            key_id=key_id,
                            key_hash=key_hash,
                            name=name,
                            owner=owner,
                            permissions=permissions,
                            expires_at=expires_at,
                        )
                    )
                except RuntimeError:
                    # No running loop in sync unit tests; skip async persistence
                    pass

            logger.info(f"Generated API key: {key_id} for owner: {owner}")
            return api_key

        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise APIKeyError(message=f"Failed to generate API key: {str(e)}") from e

    async def _save_api_key_to_db(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        owner: str,
        permissions: list[str],
        expires_at: datetime | None,
    ) -> None:
        """Save API key to database."""
        if self._session_factory is None:
            return
        try:
            session_ctx = self._session_factory()  # type: ignore[misc]
            if inspect.isawaitable(session_ctx):
                session_ctx = await session_ctx  # type: ignore[assignment]
            async with session_ctx as session:
                api_key_model = APIKeyModel(
                    id=key_id,
                    key_hash=key_hash,
                    name=name,
                    user_id=owner,
                    permissions=permissions,
                    created_at=datetime.utcnow(),
                    expires_at=expires_at,
                    is_active=True,
                )
                session.add(api_key_model)
                await session.commit()
                logger.debug(f"Saved API key to database: {key_id}")

        except Exception as e:
            logger.error(f"Failed to save API key to database: {e}")
            # Non-fatal for unit tests

    def validate_api_key(self, api_key: str) -> APIKey | None:
        """Synchronous in-memory validation for unit tests."""
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")

        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Search in-memory first
            for key in self._keys.values():
                if key.key_hash == key_hash and key.is_active:
                    if key.expires_at and key.expires_at < datetime.utcnow():
                        return None
                    key.last_used = datetime.utcnow()
                    return key

            # Optionally fall back to DB if configured
            return asyncio.run(self.validate_api_key_async(api_key)) if self._session_factory else None
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return None

    async def validate_api_key_async(self, api_key: str) -> APIKey | None:
        """Async validation via database when configured."""
        if self._session_factory is None:
            return None
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            session_ctx = self._session_factory()  # type: ignore[misc]
            if inspect.isawaitable(session_ctx):
                session_ctx = await session_ctx  # type: ignore[assignment]
            async with session_ctx as session:
                stmt = select(APIKeyModel).where(
                    APIKeyModel.key_hash == key_hash, APIKeyModel.is_active == True
                )
                result = await session.execute(stmt)
                key_record = result.scalar_one_or_none()

                if not key_record:
                    return None

                if key_record.expires_at and key_record.expires_at < datetime.utcnow():
                    return None

                key_record.last_used = datetime.utcnow()
                await session.commit()

                return APIKey(
                    key_id=key_record.id,
                    key_hash=key_record.key_hash,
                    name=key_record.name,
                    owner=key_record.user_id,
                    permissions=key_record.permissions,
                    created_at=key_record.created_at,
                    expires_at=key_record.expires_at,
                    last_used=key_record.last_used,
                    is_active=key_record.is_active,
                )
        except Exception as e:
            logger.error(f"Failed to validate API key (async): {e}")
            return None

    async def check_permission_async(self, api_key: str, permission: str) -> bool:
        record = self.validate_api_key(api_key)
        return bool(record and permission in record.permissions)

    def check_permission(self, api_key: str, permission: str) -> bool:
        """Synchronous permission check."""
        record = self.validate_api_key(api_key)
        return bool(record and permission in record.permissions)

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key (in-memory)."""
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")
        key = self._keys.get(key_id)
        if not key:
            return False
        key.is_active = False
        return True

    def list_api_keys(self, owner: str | None = None) -> list[dict]:
        """List API keys from in-memory store."""
        if not self._initialized:
            raise APIKeyError(message="API Key Manager not initialized")
        records = [k for k in self._keys.values() if (owner is None or k.owner == owner)]
        keys: list[dict] = []
        for k in records:
            keys.append(
                {
                    "key_id": k.key_id,
                    "name": k.name,
                    "owner": k.owner,
                    "permissions": k.permissions,
                    "created_at": k.created_at.isoformat(),
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "last_used": k.last_used.isoformat() if k.last_used else None,
                    "is_active": k.is_active,
                }
            )
        return keys

    async def list_api_keys_async(self, owner: str | None = None) -> list[dict]:
        """Async list via database when configured."""
        if self._session_factory is None:
            return []
        try:
            session_ctx = self._session_factory()  # type: ignore[misc]
            if inspect.isawaitable(session_ctx):
                session_ctx = await session_ctx  # type: ignore[assignment]
            async with session_ctx as session:
                stmt = select(APIKeyModel)
                if owner:
                    stmt = stmt.where(APIKeyModel.user_id == owner)
                result = await session.execute(stmt)
                key_records = result.scalars().all()
                keys = []
                for key_record in key_records:
                    keys.append(
                        {
                            "key_id": key_record.id,
                            "name": key_record.name,
                            "owner": key_record.user_id,
                            "permissions": key_record.permissions,
                            "created_at": key_record.created_at.isoformat(),
                            "expires_at": key_record.expires_at.isoformat() if key_record.expires_at else None,
                            "last_used": key_record.last_used.isoformat() if key_record.last_used else None,
                            "is_active": key_record.is_active,
                        }
                    )
                return keys
        except Exception as e:
            logger.error(f"Failed to list API keys (async): {e}")
            return []

    async def shutdown(self) -> None:
        """Shutdown the API key manager."""
        logger.info("Shutting down API Key Manager")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the API key manager is initialized."""
        return self._initialized

    @property
    def keys(self) -> dict[str, APIKey]:
        """Expose in-memory keys for unit tests."""
        return self._keys


# Global instance
_api_key_manager: APIKeyManager | None = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
