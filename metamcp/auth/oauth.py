"""
OAuth Authentication Module

This module provides OAuth 2.0 authentication support for both users and AI agents,
with specific handling for FastMCP agent authentication flows and database persistence.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..config import get_settings
from ..database.connection import get_async_session
from ..database.models import OAuthToken as OAuthTokenModel
from ..database.models import User as UserModel
from ..exceptions import OAuthError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""

    name: str = Field(..., description="Provider name")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    authorization_url: str = Field(..., description="Authorization endpoint")
    token_url: str = Field(..., description="Token endpoint")
    userinfo_url: str | None = Field(None, description="User info endpoint")
    scopes: list[str] = Field(default=["openid", "email", "profile"])
    redirect_uri: str = Field(..., description="Redirect URI")
    token_refresh_url: str | None = Field(None, description="Token refresh endpoint")

    model_config = {"extra": "forbid"}


class OAuthToken(BaseModel):
    """OAuth token model."""

    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int | None = Field(None, description="Token expiry in seconds")
    refresh_token: str | None = Field(None, description="Refresh token")
    scope: str | None = Field(None, description="Token scope")
    expires_at: datetime | None = Field(None, description="Token expiry timestamp")

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def needs_refresh(self) -> bool:
        """Check if token needs refresh (expires within 5 minutes)."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))


class OAuthUser(BaseModel):
    """OAuth user model."""

    provider: str = Field(..., description="OAuth provider")
    provider_user_id: str = Field(..., description="Provider user ID")
    email: str | None = Field(None, description="User email")
    name: str | None = Field(None, description="User name")
    picture: str | None = Field(None, description="User picture URL")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")
    is_agent: bool = Field(default=False, description="Whether user is an AI agent")


class OAuthManager:
    """
    OAuth authentication manager for users and AI agents.

    Supports multiple OAuth providers and handles both user and agent authentication
    flows, with specific optimizations for FastMCP agent authentication and
    database persistence for tokens.
    """

    def __init__(self):
        """Initialize OAuth manager."""
        self.settings = settings
        self.providers: dict[str, OAuthProvider] = {}
        self.state_store: dict[str, dict[str, Any]] = {}
        self._session_factory: sessionmaker | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize OAuth manager with configured providers."""
        try:
            logger.info("Initializing OAuth Manager...")

            # Get session factory
            self._session_factory = get_async_session()

            # Load OAuth providers from configuration
            await self._load_providers()

            # Initialize state management
            await self._initialize_state_management()

            self._initialized = True
            logger.info("OAuth Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OAuth Manager: {e}")
            raise OAuthError(
                message=f"Failed to initialize OAuth manager: {str(e)}"
            ) from e

    async def _load_providers(self) -> None:
        """Load OAuth providers from configuration."""
        try:
            # Google OAuth
            if (
                self.settings.google_oauth_client_id
                and self.settings.google_oauth_client_secret
            ):
                self.providers["google"] = OAuthProvider(
                    name="google",
                    client_id=self.settings.google_oauth_client_id,
                    client_secret=self.settings.google_oauth_client_secret,
                    authorization_url=self.settings.google_oauth_authorization_url,
                    token_url=self.settings.google_oauth_token_url,
                    userinfo_url=self.settings.google_oauth_userinfo_url,
                    scopes=["openid", "email", "profile"],
                    redirect_uri=f"{self.settings.host}/oauth/callback/google",
                )

            # GitHub OAuth
            if (
                self.settings.github_oauth_client_id
                and self.settings.github_oauth_client_secret
            ):
                self.providers["github"] = OAuthProvider(
                    name="github",
                    client_id=self.settings.github_oauth_client_id,
                    client_secret=self.settings.github_oauth_client_secret,
                    authorization_url=self.settings.github_oauth_authorization_url,
                    token_url=self.settings.github_oauth_token_url,
                    userinfo_url=self.settings.github_oauth_userinfo_url,
                    scopes=["read:user", "user:email"],
                    redirect_uri=f"{self.settings.host}/oauth/callback/github",
                )

            # Microsoft OAuth
            if (
                self.settings.microsoft_oauth_client_id
                and self.settings.microsoft_oauth_client_secret
            ):
                self.providers["microsoft"] = OAuthProvider(
                    name="microsoft",
                    client_id=self.settings.microsoft_oauth_client_id,
                    client_secret=self.settings.microsoft_oauth_client_secret,
                    authorization_url=self.settings.microsoft_oauth_authorization_url,
                    token_url=self.settings.microsoft_oauth_token_url,
                    userinfo_url=self.settings.microsoft_oauth_userinfo_url,
                    scopes=["openid", "profile", "email"],
                    redirect_uri=f"{self.settings.host}/oauth/callback/microsoft",
                )

            logger.info(
                f"Loaded {len(self.providers)} OAuth providers: {list(self.providers.keys())}"
            )

        except Exception as e:
            logger.error(f"Failed to load OAuth providers: {e}")
            raise OAuthError(message=f"Failed to load OAuth providers: {str(e)}") from e

    async def _initialize_state_management(self) -> None:
        """Initialize OAuth state management."""
        # State management is handled in memory for now
        # Could be extended to use Redis or database for distributed deployments
        pass

    def get_authorization_url(
        self,
        provider: str,
        is_agent: bool = False,
        agent_id: str | None = None,
        requested_scopes: list[str] | None = None,
    ) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            provider: OAuth provider name
            is_agent: Whether this is an agent authentication flow
            agent_id: Agent ID for agent authentication
            requested_scopes: Additional scopes to request

        Returns:
            Authorization URL
        """
        if not self._initialized:
            raise OAuthError(message="OAuth Manager not initialized")

        if provider not in self.providers:
            raise OAuthError(message=f"Unsupported OAuth provider: {provider}")

        provider_config = self.providers[provider]

        # Generate state parameter
        state = secrets.token_urlsafe(32)

        # Store state with metadata
        self.state_store[state] = {
            "provider": provider,
            "is_agent": is_agent,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow(),
            "requested_scopes": requested_scopes or [],
        }

        # Build authorization URL
        params = {
            "client_id": provider_config.client_id,
            "redirect_uri": provider_config.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": " ".join(provider_config.scopes + (requested_scopes or [])),
        }

        # Add provider-specific parameters
        if provider == "google":
            params["access_type"] = "offline"  # Request refresh token
            params["prompt"] = "consent"
        elif provider == "github":
            params["allow_signup"] = "false"

        authorization_url = f"{provider_config.authorization_url}?{urlencode(params)}"

        logger.info(f"Generated authorization URL for {provider} (agent: {is_agent})")
        return authorization_url

    async def handle_callback(
        self, provider: str, code: str, state: str, error: str | None = None
    ) -> OAuthUser:
        """
        Handle OAuth callback.

        Args:
            provider: OAuth provider name
            code: Authorization code
            state: State parameter
            error: Error parameter if any

        Returns:
            OAuthUser object
        """
        if not self._initialized:
            raise OAuthError(message="OAuth Manager not initialized")

        if error:
            raise OAuthError(message=f"OAuth error: {error}")

        # Validate state
        if state not in self.state_store:
            raise OAuthError(message="Invalid OAuth state")

        state_data = self.state_store.pop(state)

        # Check state expiration (5 minutes)
        if datetime.utcnow() - state_data["timestamp"] > timedelta(minutes=5):
            raise OAuthError(message="OAuth state expired")

        if state_data["provider"] != provider:
            raise OAuthError(message="OAuth provider mismatch")

        try:
            # Exchange code for token
            token = await self._exchange_code_for_token(provider, code, state)

            # Get user info
            user_info = await self._get_user_info(provider, token)

            # Create or update user in database
            user = await self._create_or_update_user(provider, user_info, token)

            # Store token in database
            await self._store_token(user.id, provider, token, state_data["is_agent"])

            # Create OAuthUser object
            oauth_user = OAuthUser(
                provider=provider,
                provider_user_id=user_info.get("id", user_info.get("sub", "")),
                email=user_info.get("email"),
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                scopes=token.scope.split(" ") if token.scope else [],
                is_agent=state_data["is_agent"],
            )

            logger.info(
                f"OAuth callback successful for {provider} user: {oauth_user.email}"
            )
            return oauth_user

        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            raise OAuthError(message=f"OAuth callback failed: {str(e)}") from e

    async def _exchange_code_for_token(
        self, provider: str, code: str, state: str
    ) -> OAuthToken:
        """Exchange authorization code for access token."""
        provider_config = self.providers[provider]

        async with httpx.AsyncClient() as client:
            data = {
                "client_id": provider_config.client_id,
                "client_secret": provider_config.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": provider_config.redirect_uri,
            }

            headers = {"Accept": "application/json"}

            response = await client.post(
                provider_config.token_url, data=data, headers=headers
            )

            if response.status_code != 200:
                raise OAuthError(
                    message=f"Token exchange failed: {response.status_code} - {response.text}"
                )

            token_data = response.json()

            # Calculate expiration
            expires_at = None
            if "expires_in" in token_data:
                expires_at = datetime.utcnow() + timedelta(
                    seconds=token_data["expires_in"]
                )

            return OAuthToken(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
                expires_at=expires_at,
            )

    async def _get_user_info(self, provider: str, token: OAuthToken) -> dict[str, Any]:
        """Get user information from OAuth provider."""
        provider_config = self.providers[provider]

        if not provider_config.userinfo_url:
            # For providers without userinfo endpoint, decode JWT token
            return await self._decode_jwt_token(token.access_token)

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"{token.token_type} {token.access_token}",
                "Accept": "application/json",
            }

            response = await client.get(provider_config.userinfo_url, headers=headers)

            if response.status_code != 200:
                raise OAuthError(
                    message=f"Failed to get user info: {response.status_code} - {response.text}"
                )

            return response.json()

    async def _decode_jwt_token(self, token: str) -> dict[str, Any]:
        """Decode JWT token to extract user information."""
        try:
            import jwt

            # Decode without verification for now (should verify signature in production)
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except ImportError:
            raise OAuthError(message="PyJWT library not installed")
        except Exception as e:
            raise OAuthError(message=f"Failed to decode JWT token: {str(e)}")

    async def _create_or_update_user(
        self, provider: str, user_info: dict[str, Any], token: OAuthToken
    ) -> UserModel:
        """Create or update user in database."""
        try:
            async with self._session_factory() as session:
                # Check if user exists by email
                email = user_info.get("email")
                if email:
                    stmt = select(UserModel).where(UserModel.email == email)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if user:
                        # Update existing user
                        user.last_login = datetime.utcnow()
                        await session.commit()
                        return user

                # Create new user
                user_id = str(uuid.uuid4())
                user = UserModel(
                    id=user_id,
                    username=user_info.get("name", f"{provider}_user_{user_id[:8]}"),
                    email=email,
                    full_name=user_info.get("name"),
                    hashed_password="",  # OAuth users don't have passwords
                    roles=["user"],
                    permissions={},
                    is_active=True,
                    is_admin=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(user)
                await session.commit()

                return user

        except Exception as e:
            logger.error(f"Failed to create or update user: {e}")
            raise OAuthError(
                message=f"Failed to create or update user: {str(e)}"
            ) from e

    async def _store_token(
        self, user_id: str, provider: str, token: OAuthToken, is_agent: bool
    ) -> None:
        """Store OAuth token in database."""
        try:
            async with self._session_factory() as session:
                # Check if token already exists
                stmt = select(OAuthTokenModel).where(
                    OAuthTokenModel.user_id == user_id,
                    OAuthTokenModel.provider == provider,
                )
                result = await session.execute(stmt)
                existing_token = result.scalar_one_or_none()

                if existing_token:
                    # Update existing token
                    existing_token.access_token = token.access_token
                    existing_token.refresh_token = token.refresh_token
                    existing_token.expires_at = token.expires_at
                    existing_token.scopes = (
                        token.scope.split(" ") if token.scope else []
                    )
                    existing_token.updated_at = datetime.utcnow()
                else:
                    # Create new token
                    oauth_token = OAuthTokenModel(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        provider=provider,
                        access_token=token.access_token,
                        refresh_token=token.refresh_token,
                        token_type=token.token_type,
                        expires_at=token.expires_at,
                        scopes=token.scope.split(" ") if token.scope else [],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(oauth_token)

                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store OAuth token: {e}")
            raise OAuthError(message=f"Failed to store OAuth token: {str(e)}") from e

    async def get_user_token(self, user_id: str, provider: str) -> OAuthToken | None:
        """Get OAuth token for a user."""
        if not self._initialized:
            raise OAuthError(message="OAuth Manager not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(OAuthTokenModel).where(
                    OAuthTokenModel.user_id == user_id,
                    OAuthTokenModel.provider == provider,
                )
                result = await session.execute(stmt)
                token_model = result.scalar_one_or_none()

                if not token_model:
                    return None

                # Check if token needs refresh
                if (
                    token_model.expires_at
                    and token_model.expires_at < datetime.utcnow()
                ):
                    # Token expired, try to refresh
                    refreshed_token = await self._refresh_token(provider, token_model)
                    if refreshed_token:
                        return refreshed_token
                    return None

                return OAuthToken(
                    access_token=token_model.access_token,
                    token_type=token_model.token_type,
                    expires_at=token_model.expires_at,
                    refresh_token=token_model.refresh_token,
                    scope=" ".join(token_model.scopes),
                )

        except Exception as e:
            logger.error(f"Failed to get user token: {e}")
            return None

    async def _refresh_token(
        self, provider: str, token_model: OAuthTokenModel
    ) -> OAuthToken | None:
        """Refresh OAuth token."""
        if not token_model.refresh_token:
            return None

        provider_config = self.providers[provider]

        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "client_id": provider_config.client_id,
                    "client_secret": provider_config.client_secret,
                    "refresh_token": token_model.refresh_token,
                    "grant_type": "refresh_token",
                }

                headers = {"Accept": "application/json"}

                response = await client.post(
                    provider_config.token_url, data=data, headers=headers
                )

                if response.status_code != 200:
                    logger.warning(
                        f"Token refresh failed: {response.status_code} - {response.text}"
                    )
                    return None

                token_data = response.json()

                # Update token in database
                async with self._session_factory() as session:
                    token_model.access_token = token_data["access_token"]
                    if "refresh_token" in token_data:
                        token_model.refresh_token = token_data["refresh_token"]

                    if "expires_in" in token_data:
                        token_model.expires_at = datetime.utcnow() + timedelta(
                            seconds=token_data["expires_in"]
                        )

                    token_model.updated_at = datetime.utcnow()
                    await session.commit()

                return OAuthToken(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope"),
                    expires_at=token_model.expires_at,
                )

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    async def revoke_user_token(self, user_id: str, provider: str) -> bool:
        """Revoke OAuth token for a user."""
        if not self._initialized:
            raise OAuthError(message="OAuth Manager not initialized")

        try:
            async with self._session_factory() as session:
                stmt = select(OAuthTokenModel).where(
                    OAuthTokenModel.user_id == user_id,
                    OAuthTokenModel.provider == provider,
                )
                result = await session.execute(stmt)
                token_model = result.scalar_one_or_none()

                if not token_model:
                    return False

                # Delete token from database
                await session.delete(token_model)
                await session.commit()

                logger.info(f"Revoked OAuth token for user {user_id} on {provider}")
                return True

        except Exception as e:
            logger.error(f"Failed to revoke user token: {e}")
            return False

    def get_available_providers(self) -> list[str]:
        """Get list of available OAuth providers."""
        return list(self.providers.keys())

    @property
    def is_initialized(self) -> bool:
        """Check if OAuth manager is initialized."""
        return self._initialized


# Global instance
_oauth_manager: OAuthManager | None = None


def get_oauth_manager() -> OAuthManager:
    """Get the global OAuth manager instance."""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = OAuthManager()
    return _oauth_manager
