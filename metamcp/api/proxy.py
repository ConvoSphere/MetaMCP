"""
Proxy API Endpoints

This module provides REST API endpoints for managing wrapped MCP servers,
including registration, discovery, and monitoring.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ..proxy import ProxyManager, WrappedServerConfig
from ..proxy.discovery import DiscoveryConfig, ServerDiscovery
from ..exceptions import ProxyError, ServerDiscoveryError
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/proxy", tags=["proxy"])

# Global instances
proxy_manager: Optional[ProxyManager] = None
server_discovery: Optional[ServerDiscovery] = None


# Pydantic models for API
class ServerConfigRequest(BaseModel):
    """Request model for server configuration."""
    name: str = Field(..., description="Server name")
    endpoint: str = Field(..., description="Server endpoint")
    transport: str = Field(default="http", description="Transport protocol")
    auth_required: bool = Field(default=False, description="Authentication required")
    auth_token: Optional[str] = Field(default=None, description="Authentication token")
    timeout: int = Field(default=30, description="Request timeout")
    retry_attempts: int = Field(default=3, description="Retry attempts")
    security_level: str = Field(default="medium", description="Security level")
    categories: List[str] = Field(default_factory=list, description="Tool categories")
    description: str = Field(default="", description="Server description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DiscoveryConfigRequest(BaseModel):
    """Request model for discovery configuration."""
    network_discovery: bool = Field(default=True, description="Enable network discovery")
    service_discovery: bool = Field(default=False, description="Enable service discovery")
    file_discovery: bool = Field(default=True, description="Enable file discovery")
    ports: List[int] = Field(default_factory=lambda: [8001, 8002, 8003, 8004, 8005], description="Ports to scan")
    base_urls: List[str] = Field(default_factory=lambda: ["http://localhost", "http://127.0.0.1"], description="Base URLs to scan")
    config_paths: List[str] = Field(default_factory=lambda: ["./mcp-servers.json", "./config/mcp-servers.json"], description="Config file paths")
    service_endpoints: List[str] = Field(default_factory=list, description="Service discovery endpoints")
    timeout: int = Field(default=5, description="Discovery timeout")
    max_concurrent: int = Field(default=10, description="Maximum concurrent scans")


class ServerInfoResponse(BaseModel):
    """Response model for server information."""
    server_id: str
    name: str
    endpoint: str
    transport: str
    status: str
    last_seen: str
    tool_count: int
    categories: List[str]
    security_level: str


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    server_id: str
    status: str
    last_seen: str
    healthy: bool
    error: Optional[str] = None


class DiscoveryResultResponse(BaseModel):
    """Response model for discovery results."""
    discovered_count: int
    servers: List[Dict[str, Any]]


# Dependency injection
async def get_proxy_manager() -> ProxyManager:
    """Get the proxy manager instance."""
    global proxy_manager
    if proxy_manager is None:
        proxy_manager = ProxyManager()
        await proxy_manager.initialize()
    return proxy_manager


async def get_server_discovery() -> ServerDiscovery:
    """Get the server discovery instance."""
    global server_discovery
    if server_discovery is None:
        server_discovery = ServerDiscovery()
        await server_discovery.initialize()
    return server_discovery


# API Endpoints
@router.post("/servers", response_model=Dict[str, str])
async def register_server(
    config: ServerConfigRequest,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
) -> Dict[str, str]:
    """
    Register a new MCP server for wrapping.
    
    Args:
        config: Server configuration
        
    Returns:
        Server ID
    """
    try:
        # Convert to WrappedServerConfig
        wrapped_config = WrappedServerConfig(
            name=config.name,
            endpoint=config.endpoint,
            transport=config.transport,
            auth_required=config.auth_required,
            auth_token=config.auth_token,
            timeout=config.timeout,
            retry_attempts=config.retry_attempts,
            security_level=config.security_level,
            categories=config.categories,
            description=config.description,
            metadata=config.metadata
        )
        
        server_id = await proxy_manager.register_server(wrapped_config)
        
        logger.info(f"Registered server: {server_id}")
        return {"server_id": server_id}
        
    except ProxyError as e:
        logger.error(f"Failed to register server: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error registering server: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/servers", response_model=List[ServerInfoResponse])
async def list_servers(
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
) -> List[ServerInfoResponse]:
    """
    List all registered servers.
    
    Returns:
        List of server information
    """
    try:
        servers = await proxy_manager.list_servers()
        
        return [
            ServerInfoResponse(
                server_id=server.server_id,
                name=server.name,
                endpoint=server.endpoint,
                transport=server.transport,
                status=server.status,
                last_seen=server.last_seen.isoformat(),
                tool_count=server.tool_count,
                categories=server.categories,
                security_level=server.security_level
            )
            for server in servers
        ]
        
    except Exception as e:
        logger.error(f"Failed to list servers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/servers/{server_id}", response_model=ServerInfoResponse)
async def get_server_info(
    server_id: str,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
) -> ServerInfoResponse:
    """
    Get information about a specific server.
    
    Args:
        server_id: Server ID
        
    Returns:
        Server information
    """
    try:
        server_info = await proxy_manager.get_server_info(server_id)
        
        if server_info is None:
            raise HTTPException(status_code=404, detail="Server not found")
            
        return ServerInfoResponse(
            server_id=server_info.server_id,
            name=server_info.name,
            endpoint=server_info.endpoint,
            transport=server_info.transport,
            status=server_info.status,
            last_seen=server_info.last_seen.isoformat(),
            tool_count=server_info.tool_count,
            categories=server_info.categories,
            security_level=server_info.security_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/servers/{server_id}")
async def unregister_server(
    server_id: str,
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
) -> Dict[str, str]:
    """
    Unregister a server.
    
    Args:
        server_id: Server ID to unregister
        
    Returns:
        Success message
    """
    try:
        await proxy_manager.unregister_server(server_id)
        
        logger.info(f"Unregistered server: {server_id}")
        return {"message": f"Server {server_id} unregistered successfully"}
        
    except ProxyError as e:
        logger.error(f"Failed to unregister server: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error unregistering server: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/discovery", response_model=DiscoveryResultResponse)
async def discover_servers(
    config: DiscoveryConfigRequest,
    background_tasks: BackgroundTasks,
    server_discovery: ServerDiscovery = Depends(get_server_discovery),
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
) -> DiscoveryResultResponse:
    """
    Discover MCP servers automatically.
    
    Args:
        config: Discovery configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Discovery results
    """
    try:
        # Convert to DiscoveryConfig
        discovery_config = DiscoveryConfig(
            network_discovery=config.network_discovery,
            service_discovery=config.service_discovery,
            file_discovery=config.file_discovery,
            ports=config.ports,
            base_urls=config.base_urls,
            config_paths=config.config_paths,
            service_endpoints=config.service_endpoints,
            timeout=config.timeout,
            max_concurrent=config.max_concurrent
        )
        
        # Discover servers
        discovered = await server_discovery.discover_servers(discovery_config)
        
        # Register discovered servers in background
        background_tasks.add_task(_register_discovered_servers, discovered, proxy_manager)
        
        # Convert to response format
        servers = []
        for server in discovered:
            servers.append({
                "endpoint": server.endpoint,
                "transport": server.transport,
                "name": server.name,
                "description": server.description,
                "categories": server.categories,
                "security_level": server.security_level,
                "discovered_at": server.discovered_at.isoformat()
            })
        
        logger.info(f"Discovered {len(discovered)} servers")
        
        return DiscoveryResultResponse(
            discovered_count=len(discovered),
            servers=servers
        )
        
    except ServerDiscoveryError as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during discovery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=Dict[str, HealthCheckResponse])
async def health_check(
    proxy_manager: ProxyManager = Depends(get_proxy_manager)
) -> Dict[str, HealthCheckResponse]:
    """
    Perform health check on all registered servers.
    
    Returns:
        Health check results
    """
    try:
        results = await proxy_manager.health_check()
        
        # Convert to response format
        health_results = {}
        for server_id, result in results.items():
            health_results[server_id] = HealthCheckResponse(
                server_id=server_id,
                status=result["status"],
                last_seen=result.get("last_seen", ""),
                healthy=result.get("healthy", False),
                error=result.get("error")
            )
        
        return health_results
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/discovery/servers", response_model=List[Dict[str, Any]])
async def get_discovered_servers(
    server_discovery: ServerDiscovery = Depends(get_server_discovery)
) -> List[Dict[str, Any]]:
    """
    Get all discovered servers.
    
    Returns:
        List of discovered servers
    """
    try:
        servers = await server_discovery.get_discovered_servers()
        
        # Convert to response format
        result = []
        for server in servers:
            result.append({
                "endpoint": server.endpoint,
                "transport": server.transport,
                "name": server.name,
                "description": server.description,
                "categories": server.categories,
                "security_level": server.security_level,
                "discovered_at": server.discovered_at.isoformat(),
                "metadata": server.metadata
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get discovered servers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/discovery/servers")
async def clear_discovered_servers(
    server_discovery: ServerDiscovery = Depends(get_server_discovery)
) -> Dict[str, str]:
    """
    Clear the list of discovered servers.
    
    Returns:
        Success message
    """
    try:
        await server_discovery.clear_discovered_servers()
        
        logger.info("Cleared discovered servers")
        return {"message": "Discovered servers cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear discovered servers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Background task
async def _register_discovered_servers(
    discovered: List,
    proxy_manager: ProxyManager
) -> None:
    """Register discovered servers in the background."""
    try:
        for server in discovered:
            try:
                # Convert to WrappedServerConfig
                config = await server_discovery.convert_to_wrapped_config(server)
                
                # Register with proxy manager
                await proxy_manager.register_server(config)
                
                logger.info(f"Registered discovered server: {server.name}")
                
            except Exception as e:
                logger.warning(f"Failed to register discovered server {server.name}: {e}")
                
    except Exception as e:
        logger.error(f"Background server registration failed: {e}")


# Include router in main API
def include_proxy_router(app):
    """Include the proxy router in the main FastAPI app."""
    app.include_router(router) 