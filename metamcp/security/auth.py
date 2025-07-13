"""
Authentication Manager

This module provides authentication and authorization functionality
for the MCP Meta-Server.
"""

from datetime import datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from ..config import get_settings
from ..exceptions import AuthenticationError
from ..utils.logging import get_logger

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

        # User storage (in production, this would be a database)
        self.users: dict[str, dict[str, Any]] = {
            "admin": {
                "username": "admin",
                "hashed_password": self.pwd_context.hash("admin123"),
                "role": "admin",
                "permissions": ["read", "write", "execute", "admin"]
            },
            "user": {
                "username": "user",
                "hashed_password": self.pwd_context.hash("user123"),
                "role": "user",
                "permissions": ["read", "execute"]
            }
        }

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the authentication manager."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Authentication Manager...")

            # Validate JWT secret
            if not self.settings.secret_key:
                raise AuthenticationError(
                    message="JWT secret key not configured"
                )

            self._initialized = True
            logger.info("Authentication Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Authentication Manager: {e}")
            raise AuthenticationError(
                message=f"Failed to initialize authentication manager: {str(e)}",
                error_code="auth_init_failed"
            )

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
        # Basic password strength validation
        if len(password) < 8:
            return False
        
        # Check for at least one uppercase, lowercase, and digit
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit

    def create_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
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

    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
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
            expire = datetime.utcnow() + timedelta(minutes=self.settings.access_token_expire_minutes)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
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
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )

            username: str = payload.get("sub")
            if username is None:
                raise AuthenticationError(
                    message="Invalid token: missing subject",
                    error_code="invalid_token"
                )

            return username

        except jwt.ExpiredSignatureError:
            raise AuthenticationError(
                message="Token has expired",
                error_code="token_expired"
            )
        except jwt.JWTError as e:
            raise AuthenticationError(
                message=f"Invalid token: {str(e)}",
                error_code="invalid_token"
            )

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
            raise AuthenticationError(
                message="Invalid username or password",
                error_code="invalid_credentials"
            )

        # Create access token
        access_token_expires = timedelta(hours=self.settings.jwt_expiration_hours)
        access_token = self.create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.settings.jwt_expiration_hours * 3600,
            "user": {
                "username": user["username"],
                "role": user["role"],
                "permissions": user["permissions"]
            }
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
            raise AuthenticationError(
                message="User not found",
                error_code="user_not_found"
            )

        return {
            "username": user["username"],
            "role": user["role"],
            "permissions": user["permissions"]
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
