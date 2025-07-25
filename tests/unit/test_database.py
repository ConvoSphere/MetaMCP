"""
Unit tests for database connection pooling.
"""

from unittest.mock import AsyncMock, patch

import pytest

from metamcp.utils.database import DatabaseManager, get_database_manager


class TestDatabaseManager:
    """Test database manager functionality."""

    @pytest.fixture
    def db_manager(self):
        """Create a database manager instance."""
        return DatabaseManager()

    @pytest.mark.asyncio
    async def test_initialize_without_url(self, db_manager):
        """Test initialization without database URL."""
        with patch.object(db_manager._settings, "database_url", None):
            await db_manager.initialize()
            assert not db_manager.is_initialized

    @pytest.mark.asyncio
    async def test_initialize_with_url(self, db_manager):
        """Test successful initialization with database URL."""
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock()
        mock_pool.acquire.return_value.__aexit__ = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection

        with patch("asyncpg.create_pool", return_value=mock_pool):
            with patch.object(
                db_manager._settings, "database_url", "postgresql://test"
            ):
                await db_manager.initialize()
                assert db_manager.is_initialized

    @pytest.mark.asyncio
    async def test_close(self, db_manager):
        """Test closing the database pool."""
        mock_pool = AsyncMock()
        db_manager._pool = mock_pool

        await db_manager.close()
        mock_pool.close.assert_called_once()
        assert not db_manager.is_initialized

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self, db_manager):
        """Test health check when pool is not initialized."""
        result = await db_manager.health_check()
        assert result["status"] == "unhealthy"
        assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """Test successful health check."""
        mock_pool = AsyncMock()
        mock_pool.get_size.return_value = 10
        mock_pool.get_min_size.return_value = 5
        mock_pool.get_max_size.return_value = 20
        mock_pool.get_idle_size.return_value = 8

        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 1

        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock()

        db_manager._pool = mock_pool

        result = await db_manager.health_check()
        assert result["status"] == "healthy"
        assert "response_time" in result
        assert result["test_query_result"] == 1
        assert "pool_stats" in result

    @pytest.mark.asyncio
    async def test_get_pool_stats(self, db_manager):
        """Test getting pool statistics."""
        mock_pool = AsyncMock()
        mock_pool.get_size.return_value = 10
        mock_pool.get_min_size.return_value = 5
        mock_pool.get_max_size.return_value = 20
        mock_pool.get_idle_size.return_value = 8

        db_manager._pool = mock_pool

        stats = await db_manager.get_pool_stats()
        assert stats["size"] == 10
        assert stats["min_size"] == 5
        assert stats["max_size"] == 20
        assert stats["idle_size"] == 8
        assert stats["busy_connections"] == 2

    @pytest.mark.asyncio
    async def test_execute_query(self, db_manager):
        """Test executing a query."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()

        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock()

        db_manager._pool = mock_pool

        await db_manager.execute("INSERT INTO test VALUES ($1)", "value")
        mock_connection.execute.assert_called_once_with(
            "INSERT INTO test VALUES ($1)", "value"
        )

    @pytest.mark.asyncio
    async def test_fetch_query(self, db_manager):
        """Test fetching multiple rows."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetch.return_value = [{"id": 1}, {"id": 2}]

        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock()

        db_manager._pool = mock_pool

        result = await db_manager.fetch("SELECT * FROM test")
        assert result == [{"id": 1}, {"id": 2}]
        mock_connection.fetch.assert_called_once_with("SELECT * FROM test")

    @pytest.mark.asyncio
    async def test_fetchval_query(self, db_manager):
        """Test fetching a single value."""
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = 42

        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock()

        db_manager._pool = mock_pool

        result = await db_manager.fetchval("SELECT COUNT(*) FROM test")
        assert result == 42
        mock_connection.fetchval.assert_called_once_with("SELECT COUNT(*) FROM test")


def test_get_database_manager_singleton():
    """Test that get_database_manager returns singleton."""
    manager1 = get_database_manager()
    manager2 = get_database_manager()
    assert manager1 is manager2
