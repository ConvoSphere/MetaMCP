"""
Authentication Manager

This module provides authentication and authorization functionality
for the MCP Meta-Server.
"""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import get_settings
from ..exceptions import AuthenticationError
from ..utils.logging import get_logger
from ..database.models import User
from ..database.connection import get_async_session

logger = get_logger(__name__)
settings = get_settings()


class AuthManager:
    """
    Authentication Manager for user authentication and session management.

    This class handles JWT token generation, validation, and user management.
    """

    def __init__(self, settings):
        """
        Initialize Authentication Manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the authentication manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Authentication Manager...")

            # Validate JWT secret
            if not self.settings.secret_key:
                raise AuthenticationError(message="JWT secret key not configured")

            # Check if default admin user exists, create if not
            await self._ensure_default_admin_exists()

            self._initialized = True
            logger.info("Authentication Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Authentication Manager: {e}")
            raise AuthenticationError(
                message=f"Failed to initialize authentication manager: {str(e)}"
            )

    async def _ensure_default_admin_exists(self) -> None:
        """Ensure default admin user exists in database."""
        try:
            async_session = get_async_session()
            async with async_session() as session:
                # Check if admin user exists
                admin_user = await session.get(User, "admin")

                if not admin_user:
                    # Create default admin user from environment variables
                    admin_username = self.settings.default_admin_username or "admin"
                    admin_password = self.settings.default_admin_password

                    if not admin_password:
                        logger.warning(
                            "No default admin password configured. Admin user not created."
                        )
                        return

                    # Create admin user
                    admin_user = User(
                        id=admin_username,
                        username=admin_username,
                        hashed_password=self.pwd_context.hash(admin_password),
                        role="admin",
                        permissions=["read", "write", "execute", "admin"],
                        is_active=True,
                        created_at=datetime.utcnow(),
                    )

                    session.add(admin_user)
                    await session.commit()
                    logger.info(f"Created default admin user: {admin_username}")

        except Exception as e:
            logger.error(f"Failed to ensure default admin exists: {e}")
            # Don't fail initialization for this

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user from database by username."""
        try:
            async_session = get_async_session()
            async with async_session() as session:
                user = await session.get(User, username)
                return user
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)

    def hash_password(self, password: str) -> str:
        """Generate password hash (alias for get_password_hash)."""
        return self.get_password_hash(password)

    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            True if password meets strength requirements
        """
        # Enhanced password strength validation
        if len(password) < 12:  # Increased minimum length
            return False

        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special

    def create_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT access token (alias for create_access_token).

        Args:
            data: Token payload data
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        return self.create_access_token(data, expires_delta)

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """
        Authenticate a user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User data if authentication successful, None otherwise
        """
        user = self.users.get(username)
        if not user:
            return None

        if not self.verify_password(password, user["hashed_password"]):
            return None

        return user

    def create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Token payload data
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, self.settings.secret_key, algorithm=self.settings.algorithm
        )

        return encoded_jwt

    def validate_token(self, token: str) -> str:
        """
        Validate a JWT token and return user ID.

        Args:
            token: JWT token string

        Returns:
            User ID from token

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(
                token, self.settings.secret_key, algorithms=[self.settings.algorithm]
            )

            username = payload.get("sub")
            if username is None:
                raise AuthenticationError(message="Invalid token: missing subject")

            return str(username)

        except JWTError as e:
            raise AuthenticationError(message=f"Invalid token: {str(e)}") from e

    def get_user_permissions(self, username: str) -> list:
        """
        Get user permissions.

        Args:
            username: Username

        Returns:
            List of user permissions
        """
        user = self.users.get(username)
        if not user:
            return []

        return user.get("permissions", [])

    def check_permission(self, username: str, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            username: Username
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        permissions = self.get_user_permissions(username)
        return permission in permissions

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """
        Authenticate user and return access token.

        Args:
            username: Username
            password: Plain text password

        Returns:
            Authentication response with token

        Raises:
            AuthenticationError: If authentication fails
        """
        user = self.authenticate_user(username, password)
        if not user:
            raise AuthenticationError(message="Invalid username or password")

        # Create access token
        access_token_expires = timedelta(hours=self.settings.jwt_expiration_hours)
        access_token = self.create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.settings.jwt_expiration_hours * 3600,
            "user": {
                "username": user["username"],
                "role": user["role"],
                "permissions": user["permissions"],
            },
        }

    async def logout(self, token: str) -> dict[str, str]:
        """
        Logout user (invalidate token).

        Args:
            token: JWT token to invalidate

        Returns:
            Logout response
        """
        # In a production system, you would add the token to a blacklist
        # For now, we just return a success message
        return {"message": "Successfully logged out"}

    async def get_user_info(self, username: str) -> dict[str, Any]:
        """
        Get user information.

        Args:
            username: Username

        Returns:
            User information
        """
        user = self.users.get(username)
        if not user:
            raise AuthenticationError(message="User not found")

        return {
            "username": user["username"],
            "role": user["role"],
            "permissions": user["permissions"],
        }

    async def shutdown(self) -> None:
        """Shutdown the authentication manager."""
        if not self._initialized:
            return

        logger.info("Shutting down Authentication Manager...")
        self._initialized = False
        logger.info("Authentication Manager shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized
