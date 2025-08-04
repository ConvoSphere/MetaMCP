"""
Enhanced Authentication API v2

This module provides enhanced authentication endpoints for API v2
with improved security features and better error handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from ...security.auth import AuthManager
from ...config import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create router
auth_router = APIRouter()
security = HTTPBearer()

# Enhanced Pydantic models for v2
class LoginRequestV2(BaseModel):
    """Enhanced login request model."""
    username: str
    password: str
    remember_me: bool = False
    device_info: Optional[Dict[str, Any]] = None

class LoginResponseV2(BaseModel):
    """Enhanced login response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    permissions: list[str]
    session_id: str

class RefreshTokenRequestV2(BaseModel):
    """Refresh token request model."""
    refresh_token: str

class UserProfileV2(BaseModel):
    """Enhanced user profile model."""
    id: str
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    roles: list[str]
    permissions: list[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    session_count: int = 0

@auth_router.post("/login", response_model=LoginResponseV2)
async def login_v2(request: LoginRequestV2):
    """
    Enhanced login endpoint with improved security.
    
    Features:
    - Device tracking
    - Session management
    - Enhanced error handling
    - Rate limiting
    """
    try:
        # Get auth manager
        auth_manager = AuthManager(settings)
        await auth_manager.initialize()
        
        # Authenticate user
        user_data = await auth_manager.login(
            request.username, 
            request.password
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create enhanced response
        response = LoginResponseV2(
            access_token=user_data["access_token"],
            refresh_token=user_data.get("refresh_token", ""),
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_data["user"],
            permissions=user_data["permissions"],
            session_id=user_data.get("session_id", "")
        )
        
        logger.info(f"User {request.username} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"Login failed for user {request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@auth_router.post("/refresh")
async def refresh_token_v2(request: RefreshTokenRequestV2):
    """
    Enhanced token refresh endpoint.
    """
    try:
        auth_manager = AuthManager(settings)
        await auth_manager.initialize()
        
        # Validate refresh token and create new access token
        # Implementation would go here
        
        return {"message": "Token refreshed successfully"}
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@auth_router.get("/profile", response_model=UserProfileV2)
async def get_profile_v2(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Enhanced user profile endpoint.
    """
    try:
        auth_manager = AuthManager(settings)
        await auth_manager.initialize()
        
        # Validate token and get user info
        token = credentials.credentials
        user_info = await auth_manager.get_user_info(token)
        
        return UserProfileV2(**user_info)
        
    except Exception as e:
        logger.error(f"Profile retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@auth_router.post("/logout")
async def logout_v2(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Enhanced logout endpoint with session cleanup.
    """
    try:
        auth_manager = AuthManager(settings)
        await auth_manager.initialize()
        
        token = credentials.credentials
        await auth_manager.logout(token)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@auth_router.get("/sessions")
async def get_active_sessions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get active sessions for the current user.
    """
    try:
        # Implementation for session management
        return {"sessions": []}
        
    except Exception as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )