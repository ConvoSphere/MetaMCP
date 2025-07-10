"""
Tools API Router

This module provides REST API endpoints for tool management including
registration, search, execution, and CRUD operations.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..config import get_settings
from ..exceptions import MetaMCPError, ToolNotFoundError, ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create router
tools_router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================

class ToolRegistrationRequest(BaseModel):
    """Request model for tool registration."""
    name: str = Field(..., description="Tool name (unique identifier)")
    description: str = Field(..., description="Tool description")
    endpoint: str = Field(..., description="Tool endpoint URL")
    category: str | None = Field(None, description="Tool category")
    capabilities: list[str] | None = Field(default=[], description="Tool capabilities")
    security_level: int | None = Field(default=0, description="Security level (0-10)")
    schema: dict[str, Any] | None = Field(None, description="Tool input/output schema")
    metadata: dict[str, Any] | None = Field(default={}, description="Additional metadata")
    version: str | None = Field(default="1.0.0", description="Tool version")
    author: str | None = Field(None, description="Tool author")
    tags: list[str] | None = Field(default=[], description="Tool tags")


class ToolUpdateRequest(BaseModel):
    """Request model for tool updates."""
    description: str | None = Field(None, description="Tool description")
    endpoint: str | None = Field(None, description="Tool endpoint URL")
    category: str | None = Field(None, description="Tool category")
    capabilities: list[str] | None = Field(None, description="Tool capabilities")
    security_level: int | None = Field(None, description="Security level (0-10)")
    schema: dict[str, Any] | None = Field(None, description="Tool input/output schema")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")
    version: str | None = Field(None, description="Tool version")
    tags: list[str] | None = Field(None, description="Tool tags")


class ToolSearchRequest(BaseModel):
    """Request model for tool search."""
    query: str = Field(..., description="Natural language search query")
    max_results: int | None = Field(default=10, description="Maximum number of results")
    similarity_threshold: float | None = Field(default=0.7, description="Similarity threshold")
    category: str | None = Field(None, description="Filter by category")


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    input_data: dict[str, Any] = Field(..., description="Tool input data")
    async_execution: bool | None = Field(default=False, description="Execute asynchronously")


class ToolResponse(BaseModel):
    """Response model for tool data."""
    id: str
    name: str
    description: str
    endpoint: str
    category: str | None
    capabilities: list[str]
    security_level: int
    schema: dict[str, Any] | None
    metadata: dict[str, Any]
    version: str
    author: str | None
    tags: list[str]
    created_at: str
    updated_at: str
    is_active: bool


class ToolListResponse(BaseModel):
    """Response model for tool list."""
    tools: list[ToolResponse]
    total: int
    offset: int
    limit: int


class ToolSearchResponse(BaseModel):
    """Response model for tool search."""
    tools: list[dict[str, Any]]
    query: str
    total: int
    search_time: float


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user_id() -> str:
    """Get current user ID from authentication context."""
    # TODO: Implement actual authentication
    return "system_user"


async def get_mcp_server():
    """Get MCP server instance from FastAPI app state."""
    # This will be injected by the main application
    pass


# =============================================================================
# API Endpoints
# =============================================================================

@tools_router.post(
    "",
    response_model=dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new tool"
)
async def register_tool(
    tool_data: ToolRegistrationRequest,
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    Register a new tool in the registry.
    
    Args:
        tool_data: Tool registration data
        user_id: Current user ID
        mcp_server: MCP server instance
        
    Returns:
        Tool registration result with tool ID
    """
    try:
        tool_id = await mcp_server.register_tool(
            tool_data=tool_data.dict(),
            user_id=user_id
        )

        return {"tool_id": tool_id, "message": "Tool registered successfully"}

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )


@tools_router.get(
    "",
    response_model=ToolListResponse,
    summary="List all tools"
)
async def list_tools(
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tools to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    List all available tools with pagination.
    
    Args:
        category: Optional category filter
        limit: Maximum number of tools to return
        offset: Offset for pagination
        user_id: Current user ID
        mcp_server: MCP server instance
        
    Returns:
        List of tools with pagination information
    """
    try:
        # TODO: Implement actual tool listing with MCP server
        return ToolListResponse(
            tools=[],
            total=0,
            offset=offset,
            limit=limit
        )

    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )


@tools_router.get(
    "/{tool_name}",
    response_model=ToolResponse,
    summary="Get tool details"
)
async def get_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name: Name of the tool
        user_id: Current user ID
        mcp_server: MCP server instance
        
    Returns:
        Tool details
    """
    try:
        # TODO: Implement actual tool retrieval
        raise ToolNotFoundError(tool_name)

    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )


@tools_router.put(
    "/{tool_name}",
    response_model=ToolResponse,
    summary="Update tool"
)
async def update_tool(
    tool_name: str,
    tool_data: ToolUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    Update an existing tool.
    
    Args:
        tool_name: Name of the tool to update
        tool_data: Updated tool data
        user_id: Current user ID
        mcp_server: MCP server instance
        
    Returns:
        Updated tool details
    """
    try:
        # TODO: Implement actual tool update
        raise ToolNotFoundError(tool_name)

    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )


@tools_router.delete(
    "/{tool_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tool"
)
async def delete_tool(
    tool_name: str,
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    Delete a tool from the registry.
    
    Args:
        tool_name: Name of the tool to delete
        user_id: Current user ID
        mcp_server: MCP server instance
    """
    try:
        # TODO: Implement actual tool deletion
        raise ToolNotFoundError(tool_name)

    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )


@tools_router.post(
    "/search",
    response_model=ToolSearchResponse,
    summary="Search tools"
)
async def search_tools(
    search_request: ToolSearchRequest,
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    Search for tools using semantic search.
    
    Args:
        search_request: Search parameters
        user_id: Current user ID
        mcp_server: MCP server instance
        
    Returns:
        Search results with matching tools
    """
    try:
        import time
        start_time = time.time()

        results = await mcp_server.search_tools(
            query=search_request.query,
            user_id=user_id,
            max_results=search_request.max_results,
            similarity_threshold=search_request.similarity_threshold
        )

        search_time = time.time() - start_time

        return ToolSearchResponse(
            tools=results,
            query=search_request.query,
            total=len(results),
            search_time=search_time
        )

    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )


@tools_router.post(
    "/{tool_name}/execute",
    summary="Execute tool"
)
async def execute_tool(
    tool_name: str,
    execution_request: ToolExecutionRequest,
    user_id: str = Depends(get_current_user_id),
    mcp_server = Depends(get_mcp_server)
):
    """
    Execute a tool with the provided input data.
    
    Args:
        tool_name: Name of the tool to execute
        execution_request: Tool execution parameters
        user_id: Current user ID
        mcp_server: MCP server instance
        
    Returns:
        Tool execution result
    """
    try:
        result = await mcp_server.execute_tool(
            tool_name=tool_name,
            input_data=execution_request.input_data,
            user_id=user_id
        )

        return {
            "tool_name": tool_name,
            "result": result,
            "success": True
        }

    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except MetaMCPError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
