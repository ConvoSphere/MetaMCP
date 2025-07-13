"""
Authentication Service

Business logic service for authentication operations including
user management, token handling, and permission validation.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from ..exceptions import AuthenticationError, ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Service for authentication operations.
    
    This service handles all business logic related to authentication
    including user management, token handling, and permission validation.
    """

    def __init__(self):
        """Initialize the authentication service."""
        self.users: dict[str, dict[str, Any]] = {}
        self.token_blacklist: set = set()
        self.login_history: list[dict[str, Any]] = []

        # Initialize with default users
        self._initialize_default_users()

    def _initialize_default_users(self):
        """Initialize default users for development."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        default_users = {
            "admin": {
                "username": "admin",
                "hashed_password": pwd_context.hash("admin123"),
                "user_id": "admin_user",
                "roles": ["admin"],
                "permissions": {
                    "tools": ["read", "write", "execute"],
                    "admin": ["manage"],
                    "users": ["read", "write"],
                    "system": ["monitor", "configure"]
                },
                "is_active": True,
                "created_at": datetime.now(UTC).isoformat()
            },
            "user": {
                "username": "user",
                "hashed_password": pwd_context.hash("user123"),
                "user_id": "regular_user",
                "roles": ["user"],
                "permissions": {
                    "tools": ["read", "execute"],
                    "admin": [],
                    "users": ["read"],
                    "system": []
                },
                "is_active": True,
                "created_at": datetime.now(UTC).isoformat()
            }
        }

        self.users = default_users

    async def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User data if authentication successful, None otherwise
        """
        try:
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            user = self.users.get(username)
            if not user:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None

            if not user.get("is_active", True):
                logger.warning(f"Authentication failed: user '{username}' is inactive")
                return None

            if not pwd_context.verify(password, user["hashed_password"]):
                logger.warning(f"Authentication failed: invalid password for user '{username}'")
                return None

            # Record successful login
            self._record_login(username, True)

            logger.info(f"User '{username}' authenticated successfully")
            return user

        except Exception as e:
            logger.error(f"Authentication error for user '{username}': {e}")
            self._record_login(username, False)
            return None

    async def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            JWT token string
        """
        try:
            from jose import jwt

            from ..config import get_settings

            settings = get_settings()

            to_encode = data.copy()
            if expires_delta:
                expire = datetime.now(UTC) + expires_delta
            else:
                expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

            return encoded_jwt

        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise AuthenticationError(
                message=f"Token creation failed: {str(e)}",
                error_code="token_creation_failed"
            ) from e

    async def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            from jose import JWTError, jwt

            from ..config import get_settings

            settings = get_settings()

            # Check if token is blacklisted
            if token in self.token_blacklist:
                raise AuthenticationError(
                    message="Token has been revoked",
                    error_code="token_revoked"
                )

            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")

            if username is None:
                raise AuthenticationError(
                    message="Invalid token payload",
                    error_code="invalid_token_payload"
                )

            return payload

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise AuthenticationError(
                message="Invalid token",
                error_code="invalid_token"
            ) from e
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationError(
                message=f"Token verification failed: {str(e)}",
                error_code="verification_failed"
            ) from e

    async def get_current_user(self, token: str) -> dict[str, Any]:
        """
        Get current user from token.
        
        Args:
            token: JWT token string
            
        Returns:
            User data
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        try:
            payload = await self.verify_token(token)
            username = payload.get("sub")

            if username is None:
                raise AuthenticationError(
                    message="Invalid token payload",
                    error_code="invalid_token_payload"
                )

            user = self.users.get(username)
            if user is None:
                raise AuthenticationError(
                    message="User not found",
                    error_code="user_not_found"
                )

            if not user.get("is_active", True):
                raise AuthenticationError(
                    message="User is inactive",
                    error_code="user_inactive"
                )

            return user

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Get current user failed: {e}")
            raise AuthenticationError(
                message=f"Authentication failed: {str(e)}",
                error_code="authentication_failed"
            ) from e

    async def revoke_token(self, token: str) -> None:
        """
        Revoke a token by adding it to the blacklist.
        
        Args:
            token: JWT token string
        """
        self.token_blacklist.add(token)
        logger.info("Token revoked successfully")

    async def get_user_permissions(self, user_id: str) -> dict[str, Any]:
        """
        Get user permissions.
        
        Args:
            user_id: User ID
            
        Returns:
            User permissions data
        """
        user = self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError(
                message="User not found",
                error_code="user_not_found"
            )

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "roles": user.get("roles", []),
            "permissions": user.get("permissions", {}),
            "is_active": user.get("is_active", True)
        }

    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if user has permission for a specific action on a resource.
        
        Args:
            user_id: User ID
            resource: Resource name (e.g., "tools", "admin")
            action: Action name (e.g., "read", "write", "execute")
            
        Returns:
            True if user has permission, False otherwise
        """
        user = self._get_user_by_id(user_id)
        if not user:
            return False

        permissions = user.get("permissions", {})
        resource_permissions = permissions.get(resource, [])

        # Admin users have all permissions
        if "admin" in user.get("roles", []):
            return True

        return action in resource_permissions

    async def create_user(self, user_data: dict[str, Any], created_by: str) -> str:
        """
        Create a new user.
        
        Args:
            user_data: User data
            created_by: ID of the user creating this user
            
        Returns:
            User ID
            
        Raises:
            ValidationError: If user data is invalid
        """
        try:
            from passlib.context import CryptContext

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            # Validate required fields
            required_fields = ["username", "password"]
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    raise ValidationError(
                        message=f"Missing required field: {field}",
                        error_code="missing_required_field"
                    )

            # Check for duplicate username
            if user_data["username"] in self.users:
                raise ValidationError(
                    message=f"User with username '{user_data['username']}' already exists",
                    error_code="user_already_exists"
                )

            # Create user entry
            user_id = str(uuid.uuid4())
            now = datetime.now(UTC).isoformat()

            user_entry = {
                "username": user_data["username"],
                "hashed_password": pwd_context.hash(user_data["password"]),
                "user_id": user_id,
                "roles": user_data.get("roles", ["user"]),
                "permissions": user_data.get("permissions", {
                    "tools": ["read", "execute"],
                    "admin": [],
                    "users": ["read"],
                    "system": []
                }),
                "is_active": True,
                "created_at": now,
                "created_by": created_by
            }

            self.users[user_data["username"]] = user_entry

            logger.info(f"User '{user_data['username']}' created with ID: {user_id}")
            return user_id

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            raise ValidationError(
                message=f"User creation failed: {str(e)}",
                error_code="creation_failed"
            ) from e

    async def update_user(self, user_id: str, update_data: dict[str, Any], updated_by: str) -> dict[str, Any]:
        """
        Update an existing user.
        
        Args:
            user_id: User ID
            update_data: Updated user data
            updated_by: ID of the user making the update
            
        Returns:
            Updated user data
            
        Raises:
            AuthenticationError: If user not found
        """
        user = self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError(
                message="User not found",
                error_code="user_not_found"
            )

        # Update user fields
        for key, value in update_data.items():
            if value is not None and key != "hashed_password":  # Don't allow direct password updates
                user[key] = value

        # Update password if provided
        if "password" in update_data and update_data["password"]:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user["hashed_password"] = pwd_context.hash(update_data["password"])

        # Update timestamp
        user["updated_at"] = datetime.now(UTC).isoformat()
        user["updated_by"] = updated_by

        logger.info(f"User '{user['username']}' updated by user: {updated_by}")
        return user

    async def deactivate_user(self, user_id: str, deactivated_by: str) -> None:
        """
        Deactivate a user.
        
        Args:
            user_id: User ID
            deactivated_by: ID of the user deactivating this user
            
        Raises:
            AuthenticationError: If user not found
        """
        user = self._get_user_by_id(user_id)
        if not user:
            raise AuthenticationError(
                message="User not found",
                error_code="user_not_found"
            )

        user["is_active"] = False
        user["updated_at"] = datetime.now(UTC).isoformat()
        user["deactivated_by"] = deactivated_by

        logger.info(f"User '{user['username']}' deactivated by user: {deactivated_by}")

    def _get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get user by ID from storage."""
        for user in self.users.values():
            if user["user_id"] == user_id:
                return user
        return None

    def _record_login(self, username: str, successful: bool) -> None:
        """Record login attempt."""
        login_record = {
            "username": username,
            "successful": successful,
            "timestamp": datetime.now(UTC).isoformat(),
            "ip_address": "unknown",  # Would be set from request context
            "user_agent": "unknown"   # Would be set from request context
        }
        self.login_history.append(login_record)

    def get_login_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get login history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of login history entries
        """
        return self.login_history[-limit:]

    def get_user_statistics(self) -> dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        active_users = [user for user in self.users.values() if user.get("is_active", True)]

        roles = {}
        for user in active_users:
            for role in user.get("roles", []):
                roles[role] = roles.get(role, 0) + 1

        successful_logins = len([login for login in self.login_history if login["successful"]])
        failed_logins = len([login for login in self.login_history if not login["successful"]])

        return {
            "total_users": len(self.users),
            "active_users": len(active_users),
            "roles": roles,
            "total_logins": len(self.login_history),
            "successful_logins": successful_logins,
            "failed_logins": failed_logins
        }
