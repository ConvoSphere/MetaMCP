"""
Database connection pooling utilities for MetaMCP.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from metamcp.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection pool manager."""

    def __init__(self):
        self._pool: asyncpg.Pool | None = None
        self._settings = get_settings()
        self._pool_config = {
            "min_size": 10,
            "max_size": 20,
            "command_timeout": 60,
            "server_settings": {"application_name": "metamcp", "jit": "off"},
        }

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if self._pool is not None:
            logger.warning("Database pool already initialized")
            return

        try:
            database_url = self._settings.database_url
            if not database_url:
                logger.warning(
                    "No database URL configured, skipping pool initialization"
                )
                return

            logger.info("Initializing database connection pool...")
            self._pool = await asyncpg.create_pool(database_url, **self._pool_config)

            # Test the connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            logger.info(
                f"Database pool initialized with {self._pool_config['min_size']}-{self._pool_config['max_size']} connections"
            )

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool is not None:
            logger.info("Closing database connection pool...")
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")

    @property
    def is_initialized(self) -> bool:
        """Check if the database pool is initialized."""
        return self._pool is not None

    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")

        async with self._pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise

    async def execute(self, query: str, *args) -> None:
        """Execute a query without returning results."""
        async with self.acquire() as conn:
            await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """Fetch multiple rows from a query."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        """Fetch a single row from a query."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value from a query."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def get_pool_stats(self) -> dict[str, Any]:
        """Get connection pool statistics."""
        if self._pool is None:
            return {"error": "Pool not initialized"}

        return {
            "size": self._pool.get_size(),
            "min_size": self._pool.get_min_size(),
            "max_size": self._pool.get_max_size(),
            "idle_size": self._pool.get_idle_size(),
            "busy_connections": self._pool.get_size() - self._pool.get_idle_size(),
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on the database pool."""
        if self._pool is None:
            return {"status": "unhealthy", "error": "Pool not initialized"}

        try:
            start_time = asyncio.get_event_loop().time()
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
            end_time = asyncio.get_event_loop().time()

            stats = await self.get_pool_stats()

            return {
                "status": "healthy",
                "response_time": end_time - start_time,
                "test_query_result": result,
                "pool_stats": stats,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def initialize_database() -> None:
    """Initialize the database connection pool."""
    db = get_database_manager()
    await db.initialize()


async def close_database() -> None:
    """Close the database connection pool."""
    db = get_database_manager()
    await db.close()


# Context manager for database operations
@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool."""
    db = get_database_manager()
    async with db.acquire() as conn:
        yield conn
