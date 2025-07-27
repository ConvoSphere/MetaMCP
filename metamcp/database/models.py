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

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', username='{self.username}')>"


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

    # Relationships
    created_by_user = relationship("User", back_populates="tools")
    executions = relationship("ExecutionHistory", back_populates="tool")

    def __repr__(self) -> str:
        return f"<Tool(id='{self.id}', name='{self.name}')>"


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