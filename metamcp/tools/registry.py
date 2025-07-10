"""
Tool Registry Module

This module provides tool registration, discovery, and execution functionality.
It manages tools with metadata, capabilities, and access control.
"""

from datetime import UTC, datetime
from typing import Any

from ..config import get_settings
from ..exceptions import ToolExecutionError, ToolNotFoundError, ToolRegistrationError
from ..llm.service import LLMService
from ..security.policies import PolicyEngine
from ..utils.logging import get_logger
from ..vector.client import VectorSearchClient

logger = get_logger(__name__)
settings = get_settings()


class ToolRegistry:
    """
    Tool Registry for managing MCP tools.
    
    This class handles tool registration, discovery, and execution
    with support for semantic search and access control.
    """

    def __init__(
        self,
        vector_client: VectorSearchClient,
        llm_service: LLMService,
        policy_engine: PolicyEngine
    ):
        """
        Initialize Tool Registry.
        
        Args:
            vector_client: Vector search client for semantic discovery
            llm_service: LLM service for tool descriptions
            policy_engine: Policy engine for access control
        """
        self.vector_client = vector_client
        self.llm_service = llm_service
        self.policy_engine = policy_engine

        # Tool storage
        self.tools: dict[str, dict[str, Any]] = {}
        self.tool_embeddings: dict[str, list[float]] = {}

        # Execution tracking
        self.execution_history: list[dict[str, Any]] = []

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the tool registry."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Tool Registry...")

            # Initialize vector client if available
            if self.vector_client:
                await self.vector_client.initialize()

            # Initialize LLM service if available
            if self.llm_service:
                await self.llm_service.initialize()

            # Load initial tools
            await self._load_initial_tools()

            self._initialized = True
            logger.info("Tool Registry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Tool Registry: {e}")
            raise ToolRegistrationError(
                message=f"Failed to initialize tool registry: {str(e)}",
                error_code="registry_init_failed"
            ) from e

    async def _load_initial_tools(self) -> None:
        """Load initial tools from configuration."""
        # Example tools - in production, these would come from database
        initial_tools = [
            {
                "name": "database_query",
                "description": "Execute SQL queries on various databases",
                "categories": ["database", "query"],
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to execute"},
                        "database": {"type": "string", "description": "Database name"}
                    },
                    "required": ["query"]
                },
                "endpoint": "http://db-tool:8001",
                "security_level": "medium"
            },
            {
                "name": "file_operations",
                "description": "Perform file system operations like read, write, search",
                "categories": ["filesystem", "io"],
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["read", "write", "search"]},
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Content for write operations"}
                    },
                    "required": ["operation", "path"]
                },
                "endpoint": "http://fs-tool:8002",
                "security_level": "low"
            }
        ]

        for tool in initial_tools:
            await self.register_tool(tool)

    async def register_tool(self, tool_data: dict[str, Any]) -> str:
        """
        Register a new tool.
        
        Args:
            tool_data: Tool metadata and configuration
            
        Returns:
            Tool ID
            
        Raises:
            ToolRegistrationError: If registration fails
        """
        try:
            tool_id = tool_data.get("name", f"tool_{len(self.tools)}")

            # Validate tool data
            if not tool_data.get("description"):
                raise ToolRegistrationError(
                    message="Tool description is required",
                    error_code="missing_description"
                )

            # Store tool
            self.tools[tool_id] = {
                **tool_data,
                "registered_at": datetime.now(UTC).isoformat(),
                "status": "active"
            }

            # Generate embedding for semantic search
            if self.llm_service:
                embedding = await self._generate_tool_embedding(tool_data)
                self.tool_embeddings[tool_id] = embedding

                # Store in vector database
                if self.vector_client:
                    await self.vector_client.store_embedding(
                        collection="tools",
                        id=tool_id,
                        embedding=embedding,
                        metadata=tool_data
                    )

            logger.info(f"Registered tool: {tool_id}")
            return tool_id

        except Exception as e:
            logger.error(f"Failed to register tool: {e}")
            raise ToolRegistrationError(
                message=f"Failed to register tool: {str(e)}",
                error_code="registration_failed"
            ) from e

    async def _generate_tool_embedding(self, tool_data: dict[str, Any]) -> list[float]:
        """Generate embedding for tool description."""
        try:
            description = tool_data["description"]
            categories = tool_data.get("categories", [])

            # Combine description and categories
            text = f"{description} {' '.join(categories)}"

            if self.llm_service:
                return await self.llm_service.generate_embedding(text)
            else:
                # Fallback zu SHA-256
                import hashlib
                hash_obj = hashlib.sha256(text.encode())
                hash_bytes = hash_obj.digest()

                # Convert to float values and pad/truncate to target dimension
                embedding = [float(b) / 255.0 for b in hash_bytes]
                target_size = 1536  # Default OpenAI embedding dimension

                if len(embedding) < target_size:
                    embedding.extend([0.0] * (target_size - len(embedding)))
                else:
                    embedding = embedding[:target_size]

                return embedding

        except Exception as e:
            logger.warning(f"Failed to generate tool embedding: {e}")
            return [0.0] * 1536  # Default embedding with correct dimension

    async def list_tools(self, user_id: str) -> list[dict[str, Any]]:
        """
        List available tools for a user.
        
        Args:
            user_id: User ID for access control
            
        Returns:
            List of available tools
        """
        available_tools = []

        for tool_id, tool_data in self.tools.items():
            try:
                # Check access permissions
                if await self.policy_engine.check_access(
                    user_id=user_id,
                    resource=f"tool:{tool_id}",
                    action="read"
                ):
                    available_tools.append({
                        "id": tool_id,
                        **tool_data
                    })
            except Exception as e:
                logger.warning(f"Access check failed for tool {tool_id}: {e}")
                # Include tool if access check fails (fail open)
                available_tools.append({
                    "id": tool_id,
                    **tool_data
                })

        return available_tools

    async def search_tools(
        self,
        query: str,
        user_id: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Search tools using semantic search.
        
        Args:
            query: Search query
            user_id: User ID for access control
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of matching tools
        """
        try:
            # Generate query embedding
            if self.llm_service:
                query_embedding = await self.llm_service.generate_embedding(query)
            else:
                # Fallback embedding mit SHA-256
                import hashlib
                hash_obj = hashlib.sha256(query.encode())
                hash_bytes = hash_obj.digest()

                # Convert to float values and pad/truncate to target dimension
                embedding = [float(b) / 255.0 for b in hash_bytes]
                target_size = 1536  # Default OpenAI embedding dimension

                if len(embedding) < target_size:
                    embedding.extend([0.0] * (target_size - len(embedding)))
                else:
                    embedding = embedding[:target_size]

                query_embedding = embedding

            # Search in vector database
            if self.vector_client:
                results = await self.vector_client.search(
                    collection="tools",
                    query_embedding=query_embedding,
                    limit=max_results,
                    similarity_threshold=similarity_threshold
                )

                # Filter by access permissions
                filtered_results = []
                for result in results:
                    tool_id = result["id"]
                    if await self.policy_engine.check_access(
                        user_id=user_id,
                        resource=f"tool:{tool_id}",
                        action="read"
                    ):
                        tool_data = self.tools.get(tool_id, {})
                        filtered_results.append({
                            **tool_data,
                            "similarity_score": result.get("score", 0.0)
                        })

                return filtered_results[:max_results]

            else:
                # Fallback to simple text search
                return await self._fallback_search(query, user_id, max_results)

        except Exception as e:
            logger.error(f"Tool search failed: {e}")
            return await self._fallback_search(query, user_id, max_results)

    async def _fallback_search(self, query: str, user_id: str, max_results: int) -> list[dict[str, Any]]:
        """Fallback search using simple text matching."""
        query_lower = query.lower()
        results = []

        for tool_id, tool_data in self.tools.items():
            try:
                # Check access
                if not await self.policy_engine.check_access(
                    user_id=user_id,
                    resource=f"tool:{tool_id}",
                    action="read"
                ):
                    continue

                # Simple text matching
                description = tool_data.get("description", "").lower()
                categories = [cat.lower() for cat in tool_data.get("categories", [])]

                if (query_lower in description or
                    any(query_lower in cat for cat in categories)):
                    results.append({
                        "id": tool_id,
                        **tool_data,
                        "similarity_score": 0.8  # Default score
                    })

            except Exception as e:
                logger.warning(f"Access check failed for tool {tool_id}: {e}")
                # Include if access check fails
                results.append({
                    "id": tool_id,
                    **tool_data,
                    "similarity_score": 0.8
                })

        return results[:max_results]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: str
    ) -> dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            user_id: User ID for access control
            
        Returns:
            Tool execution result
            
        Raises:
            ToolNotFoundError: If tool not found
            ToolExecutionError: If execution fails
        """
        if tool_name not in self.tools:
            raise ToolNotFoundError(
                message=f"Tool '{tool_name}' not found",
                error_code="tool_not_found"
            )

        tool_data = self.tools[tool_name]

        # Check access permissions
        if not await self.policy_engine.check_access(
            user_id=user_id,
            resource=f"tool:{tool_name}",
            action="execute"
        ):
            raise ToolExecutionError(
                message="Access denied for tool execution",
                error_code="access_denied"
            )

        try:
            # Record execution start
            start_time = datetime.now(UTC)

            # Execute tool (placeholder implementation)
            result = await self._execute_tool_internal(tool_name, arguments, tool_data)

            # Record execution end
            end_time = datetime.now(UTC)
            execution_time = (end_time - start_time).total_seconds()

            # Log execution
            self.execution_history.append({
                "tool_name": tool_name,
                "user_id": user_id,
                "arguments": arguments,
                "result": result,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            })

            return {
                "content": result,
                "is_error": False,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise ToolExecutionError(
                message=f"Tool execution failed: {str(e)}",
                error_code="execution_failed"
            ) from e

    async def _execute_tool_internal(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        tool_data: dict[str, Any]
    ) -> Any:
        """Internal tool execution implementation."""
        # This is a placeholder implementation
        # In production, this would make HTTP calls to tool endpoints

        endpoint = tool_data.get("endpoint")
        if endpoint:
            # Make HTTP call to tool endpoint
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{endpoint}/execute",
                    json={
                        "tool": tool_name,
                        "arguments": arguments
                    },
                    timeout=settings.tool_timeout
                )
                return response.json()
        else:
            # Mock execution for development
            return {
                "message": f"Executed {tool_name} with arguments: {arguments}",
                "status": "success"
            }

    async def shutdown(self) -> None:
        """Shutdown the tool registry."""
        if not self._initialized:
            return

        logger.info("Shutting down Tool Registry...")

        # Cleanup vector client
        if self.vector_client:
            await self.vector_client.shutdown()

        # Cleanup LLM service
        if self.llm_service:
            await self.llm_service.shutdown()

        self._initialized = False
        logger.info("Tool Registry shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if registry is initialized."""
        return self._initialized
