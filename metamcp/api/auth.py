"""
Authentication API Router

This module provides authentication and authorization endpoints for the
MCP Meta-Server API.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ..config import get_settings
from ..exceptions import AuthenticationError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create router
auth_router = APIRouter()

# Security scheme
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token blacklist (in production, use Redis or database)
token_blacklist: set[str] = set()

# Mock user database (in production, use actual database)
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "user_id": "admin_user",
        "roles": ["admin"],
        "permissions": ["tools:read", "tools:write", "tools:execute", "admin:manage"],
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("user123"),
        "user_id": "regular_user",
        "roles": ["user"],
        "permissions": ["tools:read", "tools:execute"],
    },
}


# =============================================================================
# Pydantic Models
# =============================================================================


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """User information model."""

    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]


# =============================================================================
# JWT Token Functions
# =============================================================================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Token payload data
        expires_delta: Optional expiration delta

    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Token payload

    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        # Check if token is blacklisted
        if token in token_blacklist:
            raise AuthenticationError("Token has been revoked")

        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise AuthenticationError("Invalid token payload")

        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User data if authentication successful, None otherwise
    """
    user = users_db.get(username)
    if not user:
        return None

    if not pwd_context.verify(password, user["hashed_password"]):
        return None

    return user


# =============================================================================
# Dependencies
# =============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Get current user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User ID

    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        username: str = payload.get("sub")

        if username is None:
            raise AuthenticationError("Invalid token payload")

        user = users_db.get(username)
        if user is None:
            raise AuthenticationError("User not found")

        return user["user_id"]

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_mcp_server():
    """Get MCP server instance from FastAPI app state."""
    # This will be injected by the main application
    pass


# =============================================================================
# API Endpoints
# =============================================================================


@auth_router.post("/login", response_model=TokenResponse, summary="User login")
async def login(login_request: LoginRequest):
    """
    Authenticate user and return access token.

    Args:
        login_request: Login credentials

    Returns:
        Access token and token information
    """
    try:
        if not login_request.username or not login_request.password:
            raise AuthenticationError("Username and password are required")

        user = authenticate_user(login_request.username, login_request.password)
        if not user:
            raise AuthenticationError("Invalid username or password")

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": e.error_code, "message": e.message}},
        )
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login",
        )


@auth_router.post("/logout", summary="User logout")
async def logout(current_user: str = Depends(get_current_user)):
    """
    Logout current user and invalidate token.

    Args:
        current_user: Current authenticated user

    Returns:
        Logout confirmation
    """
    try:
        # Add token to blacklist (in production, store in Redis/database)
        # For now, we'll just log the logout
        logger.info(f"User {current_user} logged out")

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout",
        )


@auth_router.get("/me", response_model=UserInfo, summary="Get current user info")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """
    Get information about the current authenticated user.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    try:
        # Find user by user_id
        user = None
        for u in users_db.values():
            if u["user_id"] == current_user:
                user = u
                break

        if not user:
            raise AuthenticationError("User not found")

        return UserInfo(
            user_id=user["user_id"],
            username=user["username"],
            roles=user["roles"],
            permissions=user["permissions"],
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": e.error_code, "message": e.message}},
        )
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@auth_router.get("/permissions", summary="Get user permissions")
async def get_user_permissions(current_user: str = Depends(get_current_user)):
    """
    Get permissions for the current user.

    Args:
        current_user: Current authenticated user

    Returns:
        User permissions
    """
    try:
        # Find user by user_id
        user = None
        for u in users_db.values():
            if u["user_id"] == current_user:
                user = u
                break

        if not user:
            raise AuthenticationError("User not found")

        return {
            "user_id": user["user_id"],
            "permissions": {
                "tools": [
                    perm for perm in user["permissions"] if perm.startswith("tools:")
                ],
                "admin": [
                    perm for perm in user["permissions"] if perm.startswith("admin:")
                ],
                "registry": [
                    perm for perm in user["permissions"] if perm.startswith("registry:")
                ],
            },
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": e.error_code, "message": e.message}},
        )
    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@auth_router.post(
    "/refresh", response_model=TokenResponse, summary="Refresh access token"
)
async def refresh_token(current_user: str = Depends(get_current_user)):
    """
    Refresh the access token for the current user.

    Args:
        current_user: Current authenticated user

    Returns:
        New access token
    """
    try:
        # Find user by user_id
        user = None
        for u in users_db.values():
            if u["user_id"] == current_user:
                user = u
                break

        if not user:
            raise AuthenticationError("User not found")

        # Create new access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        new_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=new_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": e.error_code, "message": e.message}},
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh",
        )
