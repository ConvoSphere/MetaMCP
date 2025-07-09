#!/usr/bin/env python3
"""
MCP Meta-Server Main Entry Point

This module provides the main entry point for the MCP Meta-Server.
It sets up the FastAPI application, initializes all components, and starts the server.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .exceptions import MetaMCPError
from .utils.logging import setup_logging, get_logger
from .server import MetaMCPServer
from .api import create_api_router
from .monitoring.metrics import setup_metrics
from .monitoring.health import setup_health_checks


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
        # Initialize the MCP server
        mcp_server = MetaMCPServer()
        await mcp_server.initialize()
        
        # Store server instance in app state
        app.state.mcp_server = mcp_server
        
        # Setup monitoring
        if settings.metrics_enabled:
            setup_metrics(app)
        
        # Setup health checks
        setup_health_checks(app, mcp_server)
        
        logger.info("MCP Meta-Server started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start MCP Meta-Server: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down MCP Meta-Server...")
        
        if hasattr(app.state, "mcp_server"):
            await app.state.mcp_server.shutdown()
        
        logger.info("MCP Meta-Server shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="MCP Meta-Server",
        description="A dynamic MCP Meta-Server for AI agents with semantic tool discovery",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.api_docs_enabled else None,
        redoc_url="/redoc" if settings.api_docs_enabled else None,
        openapi_url="/openapi.json" if settings.api_docs_enabled else None,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include API routers
    api_router = create_api_router()
    app.include_router(api_router, prefix="/api/v1")
    
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
    
    # Trusted host middleware
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", settings.host]
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup global exception handlers.
    
    Args:
        app: FastAPI application instance
    """
    @app.exception_handler(MetaMCPError)
    async def metamcp_exception_handler(request: Request, exc: MetaMCPError):
        """Handle MetaMCP specific exceptions."""
        logger.warning(f"MetaMCP error: {exc.message}", extra={"error_code": exc.error_code})
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            }
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
            }
        )


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_server() -> None:
    """
    Run the MCP Meta-Server.
    
    This is the main async entry point for running the server.
    """
    # Setup logging
    setup_logging()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Create app
    app = create_app()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.auto_reload and settings.debug,
        workers=1,  # Single worker for now to maintain state
    )
    
    # Start server
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def main() -> None:
    """
    Main entry point for the MCP Meta-Server.
    
    This function is called when running the server from the command line.
    """
    try:
        if sys.platform == "win32":
            # Windows-specific event loop policy
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the server
        asyncio.run(run_server())
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()