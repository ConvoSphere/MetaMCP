"""
Database Models

This module defines SQLAlchemy models for the MetaMCP application.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    roles = Column(JSON, nullable=False, default=list)
    permissions = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(36), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tools = relationship("Tool", back_populates="created_by_user")
    executions = relationship("ExecutionHistory", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    oauth_tokens = relationship("OAuthToken", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', username='{self.username}')>"


class APIKey(Base):
    """API Key model for API authentication."""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True)
    key_hash = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    permissions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey(id='{self.id}', name='{self.name}')>"


class Developer(Base):
    """Developer model for tool registry security."""

    __tablename__ = "developers"

    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    organization = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    registration_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    tools_created = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    verification_token = Column(String(255), nullable=True)
    verification_expires = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tools = relationship("Tool", back_populates="developer")

    def __repr__(self) -> str:
        return f"<Developer(id='{self.id}', username='{self.username}')>"


class OAuthToken(Base):
    """OAuth Token model for OAuth authentication."""

    __tablename__ = "oauth_tokens"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # google, github, microsoft
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), nullable=False, default="Bearer")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    scopes = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    user = relationship("User", back_populates="oauth_tokens")

    def __repr__(self) -> str:
        return f"<OAuthToken(id='{self.id}', provider='{self.provider}')>"


class Tool(Base):
    """Tool model for tool registration and management."""

    __tablename__ = "tools"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    endpoint = Column(String(500), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    capabilities = Column(JSON, nullable=False, default=list)
    security_level = Column(Integer, default=0, nullable=False)
    schema = Column(JSON, nullable=True)
    tool_metadata = Column(JSON, nullable=False, default=dict)
    version = Column(String(50), default="1.0.0", nullable=False)
    author = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    developer_id = Column(String(36), ForeignKey("developers.id"), nullable=True)

    # Relationships
    created_by_user = relationship("User", back_populates="tools")
    developer = relationship("Developer", back_populates="tools")
    executions = relationship("ExecutionHistory", back_populates="tool")
    versions = relationship("ToolVersion", back_populates="tool")

    def __repr__(self) -> str:
        return f"<Tool(id='{self.id}', name='{self.name}')>"


class ToolVersion(Base):
    """Tool Version model for version management."""

    __tablename__ = "tool_versions"

    id = Column(String(36), primary_key=True)
    tool_id = Column(String(36), ForeignKey("tools.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    schema = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    deprecation_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    tool = relationship("Tool", back_populates="versions")

    __table_args__ = (
        UniqueConstraint('tool_id', 'version', name='uq_tool_version'),
    )

    def __repr__(self) -> str:
        return f"<ToolVersion(id='{self.id}', tool_id='{self.tool_id}', version='{self.version}')>"


class Workflow(Base):
    """Workflow model for composition engine."""

    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    definition = Column(JSON, nullable=False)
    version = Column(String(50), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow")

    def __repr__(self) -> str:
        return f"<Workflow(id='{self.id}', name='{self.name}')>"


class WorkflowExecution(Base):
    """Workflow Execution model for tracking workflow runs."""

    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # running, completed, failed, cancelled
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id='{self.id}', workflow_id='{self.workflow_id}', status='{self.status}')>"


class ExecutionHistory(Base):
    """Execution history model for tracking tool executions."""

    __tablename__ = "execution_history"

    id = Column(String(36), primary_key=True)
    tool_id = Column(String(36), ForeignKey("tools.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    arguments = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, index=True)  # success, failed, timeout
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    tool = relationship("Tool", back_populates="executions")
    user = relationship("User", back_populates="executions")

    def __repr__(self) -> str:
        return f"<ExecutionHistory(id='{self.id}', tool_id='{self.tool_id}', status='{self.status}')>"


class SearchHistory(Base):
    """Search history model for tracking search operations."""

    __tablename__ = "search_history"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False, index=True)  # semantic, keyword, hybrid
    max_results = Column(Integer, nullable=False)
    similarity_threshold = Column(Integer, nullable=True)  # stored as percentage
    result_count = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=True)  # milliseconds
    status = Column(String(50), nullable=False, index=True)  # completed, failed, timeout
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self) -> str:
        return f"<SearchHistory(id='{self.id}', query='{self.query[:50]}...', status='{self.status}')>"


class VectorEmbedding(Base):
    """Vector embedding model for storing tool embeddings."""

    __tablename__ = "vector_embeddings"

    id = Column(String(36), primary_key=True)
    tool_id = Column(String(36), ForeignKey("tools.id"), nullable=False, index=True)
    embedding = Column(JSON, nullable=False)  # List of floats
    embedding_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self) -> str:
        return f"<VectorEmbedding(id='{self.id}', tool_id='{self.tool_id}')>"


class AuditLog(Base):
    """Audit Log model for security and compliance."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Index for efficient querying
    __table_args__ = (
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id='{self.id}', action='{self.action}', resource_type='{self.resource_type}')>"


class ResourceLimit(Base):
    """Resource Limit model for rate limiting and quotas."""

    __tablename__ = "resource_limits"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # api_calls, tool_executions, etc.
    limit_value = Column(Integer, nullable=False)
    current_usage = Column(Integer, nullable=False, default=0)
    reset_period = Column(String(20), nullable=False)  # daily, monthly, etc.
    reset_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('user_id', 'resource_type', name='uq_user_resource_limit'),
    )

    def __repr__(self) -> str:
        return f"<ResourceLimit(id='{self.id}', user_id='{self.user_id}', resource_type='{self.resource_type}')>"