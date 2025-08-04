#!/usr/bin/env python3
"""
MCP Meta-Server Main Entry Point

This module provides the main entry point for the MCP Meta-Server.
It sets up the FastAPI application, initializes all components, and starts the server.
"""

import asyncio
import signal
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .api import create_api_router, get_api_version_manager
from .cache.redis_cache import close_cache_manager
from .config import get_settings
from .exceptions import MetaMCPError
from .monitoring.health import setup_health_checks
from .monitoring.metrics import setup_metrics
from .monitoring.performance import performance_monitor
from .performance.background_tasks import start_background_tasks, stop_background_tasks
from .performance.connection_pool import close_database_pool
from .performance.circuit_breaker import circuit_breaker_manager
from .services.service_discovery import service_discovery, ServiceType
from .security.middleware import SecurityMiddleware, RateLimitMiddleware
from .server import MetaMCPServer
from .utils.logging import get_logger, setup_logging

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown of the MCP Meta-Server components.
    """
    logger.info("Starting MCP Meta-Server...")

    try:
        # Initialize database connection pool
        from .utils.database import initialize_database

        await initialize_database()
        logger.info("Database connection pool initialized")

        # Initialize API Version Manager
        version_manager = get_api_version_manager()
        await version_manager.initialize()
        logger.info("API Version Manager initialized")

        # Initialize the MCP server
        mcp_server = MetaMCPServer()
        await mcp_server.initialize()

        # Store server instance in app state
        app.state.mcp_server = mcp_server
        app.state.version_manager = version_manager

        # Start service discovery
        await service_discovery.start()
        logger.info("Service discovery started")

        # Start performance monitoring
        await performance_monitor.start()
        logger.info("Performance monitoring started")

        # Register this service with service discovery
        await service_discovery.register_service(
            service_id="metamcp-api",
            name="MetaMCP API Server",
            service_type=ServiceType.API,
            host=settings.host,
            port=settings.port,
            version=settings.app_version,
            health_check_url=f"http://{settings.host}:{settings.port}/health",
            metadata={
                "environment": settings.environment,
                "debug": settings.debug,
                "api_versions": version_manager.get_active_versions(),
            },
            tags=["api", "mcp", "metamcp"],
        )
        logger.info("Service registered with service discovery")

        # Setup monitoring
        if settings.telemetry_enabled:
            setup_metrics(app)

        # Setup health checks
        setup_health_checks(app, mcp_server)

        # Start background task manager
        await start_background_tasks()
        logger.info("Background task manager started")

        logger.info("MCP Meta-Server started successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start MCP Meta-Server: {e}")
        raise

    finally:
        logger.info("Shutting down MCP Meta-Server...")

        try:
            # Stop background tasks
            await stop_background_tasks()
            logger.info("Background task manager stopped")

            # Stop performance monitoring
            await performance_monitor.stop()
            logger.info("Performance monitoring stopped")

            # Stop service discovery
            await service_discovery.stop()
            logger.info("Service discovery stopped")

            # Close database pool
            await close_database_pool()
            logger.info("Database connection pool closed")

            # Close cache manager
            await close_cache_manager()
            logger.info("Cache manager closed")

            # Shutdown version manager
            if hasattr(app.state, 'version_manager'):
                await app.state.version_manager.shutdown()
            logger.info("API Version Manager shutdown")

            logger.info("MCP Meta-Server shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="MCP Meta-Server",
        description="A dynamic MCP Meta-Server for AI agents with semantic tool discovery and API versioning",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    # Add middleware
    setup_middleware(app)

    # Add exception handlers
    setup_exception_handlers(app)

    # Include API routers with versioning
    api_router = create_api_router()
    app.include_router(api_router)

    return app


def setup_middleware(app: FastAPI) -> None:
    """
    Setup FastAPI middleware.

    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Trusted host middleware (only in production)
    if not settings.debug and settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", settings.host],
        )

    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup global exception handlers.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(MetaMCPError)
    async def metamcp_exception_handler(request: Request, exc: MetaMCPError):
        """Handle MetaMCP specific exceptions."""
        logger.warning(
            f"MetaMCP error: {exc.message}", extra={"error_code": exc.error_code}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An internal server error occurred",
                    "details": str(exc) if settings.debug else None,
                }
            },
        )


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_server() -> None:
    """Run the FastAPI server."""
    setup_logging()
    setup_signal_handlers()

    app = create_app()

    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True,
    )

    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
