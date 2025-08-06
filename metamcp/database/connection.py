"""
Database Connection Management

This module provides database connection management and session handling.
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config import get_settings

settings = get_settings()


def get_database_url() -> str:
    """Get database URL from settings."""
    return settings.database_url


def create_engine():
    """Create database engine."""
    database_url = get_database_url()
    
    if database_url.startswith("sqlite"):
        # SQLite configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=settings.debug,
        )
    else:
        # PostgreSQL/MySQL configuration
        engine = create_engine(
            database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            echo=settings.debug,
        )
    
    return engine


def create_async_engine_instance():
    """Create async database engine."""
    database_url = get_database_url()
    
    if database_url.startswith("sqlite"):
        # Convert to async SQLite URL
        async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        engine = create_async_engine(async_url)
    else:
        # PostgreSQL/MySQL async configuration
        async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(
            async_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
        )
    
    return engine


def get_session():
    """Get database session factory."""
    engine = create_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def get_async_session():
    """Get async database session factory."""
    engine = create_async_engine_instance()
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async_session = get_async_session()
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()