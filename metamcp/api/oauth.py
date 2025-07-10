"""
OAuth API Endpoints

This module provides OAuth API endpoints for both user and agent authentication,
with specific support for FastMCP agent authentication flows.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth.oauth import OAuthUser, get_oauth_manager
from ..exceptions import MetaMCPException
from ..security.auth import get_current_user
from ..utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth"])


class OAuthInitiateRequest(BaseModel):
    """Request model for initiating OAuth flow."""

    provider: str = Field(..., description="OAuth provider name")
    is_agent: bool = Field(default=False, description="Whether this is an agent authentication")
    agent_id: str | None = Field(None, description="Agent ID for agent-specific flows")
    requested_scopes: list[str] | None = Field(None, description="Requested OAuth scopes")
    redirect_uri: str | None = Field(None, description="Custom redirect URI")


class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback."""

    success: bool = Field(..., description="Whether authentication was successful")
    user: OAuthUser | None = Field(None, description="OAuth user information")
    access_token: str | None = Field(None, description="JWT access token")
    error: str | None = Field(None, description="Error message if failed")


class AgentOAuthStatus(BaseModel):
    """Agent OAuth session status."""

    agent_id: str = Field(..., description="Agent ID")
    provider: str = Field(..., description="OAuth provider")
    is_authenticated: bool = Field(..., description="Whether agent is authenticated")
    expires_at: str | None = Field(None, description="Session expiry timestamp")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")


@router.get("/providers")
async def list_oauth_providers() -> dict[str, list[str]]:
    """List available OAuth providers."""
    try:
        oauth_manager = get_oauth_manager()
        providers = oauth_manager.get_available_providers()

        return {
            "providers": providers,
            "total": len(providers)
        }

    except Exception as e:
        logger.error(f"Failed to list OAuth providers: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list OAuth providers"
        )


@router.post("/initiate")
async def initiate_oauth_flow(request: OAuthInitiateRequest) -> dict[str, str]:
    """Initiate OAuth authentication flow."""
    try:
        oauth_manager = get_oauth_manager()

        # Get authorization URL
        auth_url = oauth_manager.get_authorization_url(
            provider=request.provider,
            is_agent=request.is_agent,
            agent_id=request.agent_id,
            requested_scopes=request.requested_scopes
        )

        return {
            "authorization_url": auth_url,
            "provider": request.provider,
            "is_agent": request.is_agent
        }

    except MetaMCPException as e:
        logger.error(f"OAuth initiation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to initiate OAuth flow: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate OAuth flow"
        )


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None
) -> OAuthCallbackResponse:
    """Handle OAuth callback."""
    try:
        oauth_manager = get_oauth_manager()

        if error:
            return OAuthCallbackResponse(
                success=False,
                error=f"OAuth authorization failed: {error}"
            )

        if not code or not state:
            return OAuthCallbackResponse(
                success=False,
                error="Missing required OAuth parameters"
            )

        # Handle OAuth callback
        oauth_user = await oauth_manager.handle_callback(
            provider=provider,
            code=code,
            state=state,
            error=error
        )

        # Generate JWT token for the user
        from ..security.auth import get_auth_manager
        auth_manager = get_auth_manager()

        user_data = {
            "user_id": f"{provider}:{oauth_user.provider_user_id}",
            "username": oauth_user.email or oauth_user.name,
            "email": oauth_user.email,
            "provider": provider,
            "is_agent": oauth_user.is_agent,
            "scopes": oauth_user.scopes
        }

        access_token = await auth_manager.create_token(user_data)

        return OAuthCallbackResponse(
            success=True,
            user=oauth_user,
            access_token=access_token
        )

    except MetaMCPException as e:
        logger.error(f"OAuth callback failed: {e}")
        return OAuthCallbackResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to handle OAuth callback: {e}")
        return OAuthCallbackResponse(
            success=False,
            error="Internal server error"
        )


@router.get("/agent/{agent_id}/status")
async def get_agent_oauth_status(
    agent_id: str,
    provider: str,
    current_user: dict[str, Any] = Depends(get_current_user)
) -> AgentOAuthStatus:
    """Get OAuth session status for an agent."""
    try:
        oauth_manager = get_oauth_manager()

        # Check if agent session is valid
        is_authenticated = await oauth_manager.validate_agent_session(agent_id, provider)

        # Get token information
        token = await oauth_manager.get_agent_token(agent_id, provider)

        return AgentOAuthStatus(
            agent_id=agent_id,
            provider=provider,
            is_authenticated=is_authenticated,
            expires_at=token.expires_at.isoformat() if token and token.expires_at else None,
            scopes=token.scope.split(" ") if token and token.scope else []
        )

    except Exception as e:
        logger.error(f"Failed to get agent OAuth status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get agent OAuth status"
        )


@router.post("/agent/{agent_id}/revoke")
async def revoke_agent_oauth_session(
    agent_id: str,
    provider: str,
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    """Revoke OAuth session for an agent."""
    try:
        oauth_manager = get_oauth_manager()

        await oauth_manager.revoke_agent_session(agent_id, provider)

        return {
            "message": f"OAuth session revoked for agent {agent_id} ({provider})"
        }

    except Exception as e:
        logger.error(f"Failed to revoke agent OAuth session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke agent OAuth session"
        )


@router.get("/agent/{agent_id}/token")
async def get_agent_oauth_token(
    agent_id: str,
    provider: str,
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Get OAuth token for an agent (for FastMCP integration)."""
    try:
        oauth_manager = get_oauth_manager()

        token = await oauth_manager.get_agent_token(agent_id, provider)

        if not token:
            raise HTTPException(
                status_code=404,
                detail=f"No OAuth token found for agent {agent_id} ({provider})"
            )

        return {
            "agent_id": agent_id,
            "provider": provider,
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scope": token.scope
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent OAuth token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get agent OAuth token"
        )


# FastMCP-specific OAuth endpoints

@router.post("/fastmcp/agent/authenticate")
async def fastmcp_agent_authenticate(
    agent_id: str,
    provider: str,
    requested_scopes: list[str] | None = None
) -> dict[str, str]:
    """Initiate OAuth authentication for FastMCP agent."""
    try:
        oauth_manager = get_oauth_manager()

        # Generate authorization URL for agent
        auth_url = oauth_manager.get_authorization_url(
            provider=provider,
            is_agent=True,
            agent_id=agent_id,
            requested_scopes=requested_scopes
        )

        return {
            "authorization_url": auth_url,
            "agent_id": agent_id,
            "provider": provider,
            "flow_type": "agent_oauth"
        }

    except Exception as e:
        logger.error(f"Failed to initiate FastMCP agent OAuth: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate agent OAuth flow"
        )


@router.get("/fastmcp/agent/{agent_id}/session")
async def fastmcp_agent_session_status(agent_id: str, provider: str) -> dict[str, Any]:
    """Get FastMCP agent OAuth session status."""
    try:
        oauth_manager = get_oauth_manager()

        # Check session validity
        is_valid = await oauth_manager.validate_agent_session(agent_id, provider)

        if not is_valid:
            return {
                "agent_id": agent_id,
                "provider": provider,
                "authenticated": False,
                "message": "Agent session not found or expired"
            }

        # Get token information
        token = await oauth_manager.get_agent_token(agent_id, provider)

        return {
            "agent_id": agent_id,
            "provider": provider,
            "authenticated": True,
            "expires_at": token.expires_at.isoformat() if token and token.expires_at else None,
            "scopes": token.scope.split(" ") if token and token.scope else []
        }

    except Exception as e:
        logger.error(f"Failed to get FastMCP agent session status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get agent session status"
        )


@router.post("/fastmcp/agent/{agent_id}/token")
async def fastmcp_agent_token_exchange(
    agent_id: str,
    provider: str,
    authorization_code: str,
    state: str
) -> dict[str, Any]:
    """Exchange authorization code for agent token (FastMCP integration)."""
    try:
        oauth_manager = get_oauth_manager()

        # Handle OAuth callback for agent
        oauth_user = await oauth_manager.handle_callback(
            provider=provider,
            code=authorization_code,
            state=state
        )

        # Verify this is an agent authentication
        if not oauth_user.is_agent:
            raise HTTPException(
                status_code=400,
                detail="This endpoint is for agent authentication only"
            )

        # Get the stored token
        token = await oauth_manager.get_agent_token(agent_id, provider)

        if not token:
            raise HTTPException(
                status_code=404,
                detail="Agent token not found"
            )

        return {
            "agent_id": agent_id,
            "provider": provider,
            "access_token": token.access_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scope": token.scope,
            "user": {
                "provider_user_id": oauth_user.provider_user_id,
                "email": oauth_user.email,
                "name": oauth_user.name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to exchange agent token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to exchange authorization code for token"
        )


# OAuth configuration endpoints

@router.get("/config")
async def get_oauth_configuration() -> dict[str, Any]:
    """Get OAuth configuration information."""
    try:
        oauth_manager = get_oauth_manager()

        return {
            "providers": oauth_manager.get_available_providers(),
            "agent_oauth_enabled": True,
            "fastmcp_integration": True,
            "supported_scopes": {
                "google": ["openid", "email", "profile"],
                "github": ["read:user", "user:email"],
                "microsoft": ["openid", "profile", "email"]
            }
        }

    except Exception as e:
        logger.error(f"Failed to get OAuth configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get OAuth configuration"
        )
