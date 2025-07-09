"""
Configuration Management for MCP Meta-Server

This module handles all configuration settings using Pydantic Settings,
which automatically loads values from environment variables, .env files,
and provides type validation and defaults.
"""

import os
from functools import lru_cache
from typing import List, Optional, Any, Dict
from enum import Enum

from pydantic import BaseSettings, Field, validator, SecretStr
from pydantic.types import PositiveInt


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    AZURE = "azure"


class PolicyEngine(str, Enum):
    """Supported policy engines."""
    OPA = "opa"
    CASBIN = "casbin"
    INTERNAL = "internal"


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables with the
    prefix specified in the Config class.
    """
    
    # =============================================================================
    # Server Configuration
    # =============================================================================
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: PositiveInt = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    secret_key: SecretStr = Field(description="Secret key for encryption")
    
    # =============================================================================
    # Database Configuration
    # =============================================================================
    
    database_url: str = Field(description="Database connection URL")
    database_pool_size: PositiveInt = Field(default=20, description="Database pool size")
    database_max_overflow: PositiveInt = Field(default=30, description="Database max overflow")
    
    # =============================================================================
    # Vector Database (Weaviate)
    # =============================================================================
    
    weaviate_url: str = Field(default="http://localhost:8088", description="Weaviate URL")
    weaviate_api_key: Optional[str] = Field(default=None, description="Weaviate API key")
    weaviate_scheme: Optional[str] = Field(default=None, description="Weaviate scheme")
    weaviate_timeout: PositiveInt = Field(default=30, description="Weaviate timeout")
    
    # =============================================================================
    # Redis Configuration
    # =============================================================================
    
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_pool_size: PositiveInt = Field(default=10, description="Redis pool size")
    
    # =============================================================================
    # LLM Configuration
    # =============================================================================
    
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM provider")
    
    # OpenAI
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", description="OpenAI embedding model")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    ollama_model: str = Field(default="llama2", description="Ollama model")
    ollama_embedding_model: str = Field(default="nomic-embed-text", description="Ollama embedding model")
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    azure_openai_api_key: Optional[SecretStr] = Field(default=None, description="Azure OpenAI API key")
    azure_openai_api_version: str = Field(default="2023-05-15", description="Azure OpenAI API version")
    azure_openai_deployment_name: Optional[str] = Field(default=None, description="Azure OpenAI deployment name")
    
    # =============================================================================
    # Policy Engine Configuration
    # =============================================================================
    
    opa_url: str = Field(default="http://localhost:8181", description="OPA server URL")
    opa_policy_path: str = Field(default="/v1/data/metamcp", description="OPA policy path")
    policy_engine: PolicyEngine = Field(default=PolicyEngine.OPA, description="Policy engine type")
    
    # =============================================================================
    # Security Configuration
    # =============================================================================
    
    jwt_secret_key: SecretStr = Field(description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: PositiveInt = Field(default=24, description="JWT expiration hours")
    password_min_length: PositiveInt = Field(default=8, description="Minimum password length")
    cors_origins: List[str] = Field(default=[], description="CORS allowed origins")
    
    # =============================================================================
    # Audit & Logging
    # =============================================================================
    
    audit_log_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_level: LogLevel = Field(default=LogLevel.INFO, description="Audit log level")
    structured_logging: bool = Field(default=True, description="Enable structured logging")
    log_file_path: str = Field(default="./logs/metamcp.log", description="Log file path")
    log_rotation_size: str = Field(default="100MB", description="Log rotation size")
    log_retention_days: PositiveInt = Field(default=30, description="Log retention days")
    
    # =============================================================================
    # Monitoring & Metrics
    # =============================================================================
    
    metrics_enabled: bool = Field(default=True, description="Enable metrics")
    prometheus_metrics_port: PositiveInt = Field(default=9000, description="Prometheus metrics port")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    health_check_interval: PositiveInt = Field(default=30, description="Health check interval")
    
    # =============================================================================
    # MCP Protocol Configuration
    # =============================================================================
    
    mcp_websocket_enabled: bool = Field(default=True, description="Enable MCP WebSocket")
    mcp_websocket_path: str = Field(default="/mcp/ws", description="MCP WebSocket path")
    mcp_max_connections: PositiveInt = Field(default=100, description="Max MCP connections")
    mcp_connection_timeout: PositiveInt = Field(default=300, description="MCP connection timeout")
    
    # =============================================================================
    # Tool Management
    # =============================================================================
    
    tool_discovery_enabled: bool = Field(default=True, description="Enable tool discovery")
    tool_health_check_interval: PositiveInt = Field(default=60, description="Tool health check interval")
    tool_timeout: PositiveInt = Field(default=30, description="Tool timeout")
    max_concurrent_tool_calls: PositiveInt = Field(default=10, description="Max concurrent tool calls")
    
    # =============================================================================
    # Vector Search Configuration
    # =============================================================================
    
    vector_dimension: PositiveInt = Field(default=1536, description="Vector dimension")
    similarity_threshold: float = Field(default=0.7, description="Similarity threshold")
    max_search_results: PositiveInt = Field(default=10, description="Max search results")
    search_timeout: PositiveInt = Field(default=5, description="Search timeout")
    
    # =============================================================================
    # Rate Limiting
    # =============================================================================
    
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: PositiveInt = Field(default=60, description="Rate limit per minute")
    rate_limit_burst: PositiveInt = Field(default=100, description="Rate limit burst")
    
    # =============================================================================
    # Development Settings
    # =============================================================================
    
    dev_mode: bool = Field(default=False, description="Development mode")
    auto_reload: bool = Field(default=False, description="Auto reload")
    api_docs_enabled: bool = Field(default=True, description="Enable API docs")
    profiling_enabled: bool = Field(default=False, description="Enable profiling")
    
    # =============================================================================
    # Admin UI Configuration
    # =============================================================================
    
    admin_ui_enabled: bool = Field(default=True, description="Enable admin UI")
    admin_ui_path: str = Field(default="/admin", description="Admin UI path")
    admin_ui_secret_key: SecretStr = Field(description="Admin UI secret key")
    
    # =============================================================================
    # Validators
    # =============================================================================
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @validator("secret_key", "jwt_secret_key", "admin_ui_secret_key")
    def validate_secret_keys(cls, v):
        """Validate secret keys are not empty."""
        if isinstance(v, SecretStr):
            secret = v.get_secret_value()
        else:
            secret = v
        
        if not secret or secret.startswith("your-"):
            raise ValueError("Secret keys must be set and not use default values")
        
        return v
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v, values):
        """Validate OpenAI API key when using OpenAI provider."""
        if values.get("llm_provider") == LLMProvider.OPENAI and not v:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        return v
    
    # =============================================================================
    # Configuration
    # =============================================================================
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def prepare_field(cls, field) -> None:
            """Prepare field for environment variable parsing."""
            if 'env_names' in field.field_info.extra:
                return
            field.field_info.extra['env_names'] = {
                field.name.upper(),
                f"METAMCP_{field.name.upper()}"
            }
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def get_database_url(self) -> str:
        """Get database URL with environment substitution."""
        return self.database_url
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key as string."""
        return self.openai_api_key.get_secret_value() if self.openai_api_key else None
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key as string."""
        return self.jwt_secret_key.get_secret_value()
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and not self.dev_mode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary, excluding secrets."""
        data = self.dict()
        
        # Remove secret fields
        for field_name, field in self.__fields__.items():
            if field.type_ == SecretStr or "secret" in field_name.lower():
                data[field_name] = "***"
        
        return data


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()