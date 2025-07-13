"""
Search Service

Business logic service for search operations including
semantic search, vector search, and search result processing.
"""

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
import time

from ..exceptions import SearchError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """
    Service for search operations.
    
    This service handles all business logic related to search including
    semantic search, vector search, and search result processing.
    """

    def __init__(self):
        """Initialize the search service."""
        self.search_history: List[Dict[str, Any]] = []
        self.search_metrics: Dict[str, Any] = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "average_response_time": 0.0
        }

    async def search_tools(
        self,
        query: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        search_type: str = "semantic"
    ) -> Dict[str, Any]:
        """
        Search for tools using various search methods.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            similarity_threshold: Similarity threshold for vector search
            search_type: Type of search ("semantic", "keyword", "hybrid")
            
        Returns:
            Search results with metadata
        """
        try:
            start_time = time.time()
            
            # Record search attempt
            search_id = self._generate_search_id()
            search_record = {
                "search_id": search_id,
                "query": query,
                "max_results": max_results,
                "similarity_threshold": similarity_threshold,
                "search_type": search_type,
                "start_time": datetime.now(UTC).isoformat(),
                "status": "in_progress"
            }
            self.search_history.append(search_record)
            
            # Perform search based on type
            if search_type == "semantic":
                results = await self._semantic_search(query, max_results, similarity_threshold)
            elif search_type == "keyword":
                results = await self._keyword_search(query, max_results)
            elif search_type == "hybrid":
                results = await self._hybrid_search(query, max_results, similarity_threshold)
            else:
                raise SearchError(
                    message=f"Unsupported search type: {search_type}",
                    error_code="unsupported_search_type"
                )
            
            # Calculate search duration
            duration = time.time() - start_time
            
            # Update search record
            search_record.update({
                "status": "completed",
                "duration": duration,
                "result_count": len(results),
                "end_time": datetime.now(UTC).isoformat()
            })
            
            # Update metrics
            self._update_search_metrics(duration, True)
            
            logger.info(f"Search completed in {duration:.3f}s, found {len(results)} results")
            
            return {
                "search_id": search_id,
                "query": query,
                "search_type": search_type,
                "results": results,
                "total": len(results),
                "search_time": duration,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            # Update search record with error
            if 'search_record' in locals():
                search_record.update({
                    "status": "failed",
                    "error": str(e),
                    "end_time": datetime.now(UTC).isoformat()
                })
            
            # Update metrics
            self._update_search_metrics(0.0, False)
            
            logger.error(f"Search failed: {e}")
            raise SearchError(
                message=f"Search failed: {str(e)}",
                error_code="search_failed"
            ) from e

    async def _semantic_search(
        self,
        query: str,
        max_results: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            similarity_threshold: Similarity threshold
            
        Returns:
            List of search results
        """
        try:
            # This would integrate with a vector database like Pinecone or Weaviate
            # For now, we'll use a simple text-based similarity
            
            # Get all available tools (this would come from tool registry)
            all_tools = self._get_available_tools()
            
            # Calculate similarity scores
            scored_results = []
            for tool in all_tools:
                score = self._calculate_similarity(query, tool)
                if score >= similarity_threshold:
                    scored_results.append({
                        "tool": tool,
                        "score": score,
                        "match_type": "semantic"
                    })
            
            # Sort by score and limit results
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            results = scored_results[:max_results]
            
            # Format results
            return [
                {
                    "id": result["tool"]["id"],
                    "name": result["tool"]["name"],
                    "description": result["tool"]["description"],
                    "category": result["tool"].get("category"),
                    "score": result["score"],
                    "match_type": result["match_type"]
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            # Get all available tools
            all_tools = self._get_available_tools()
            
            # Simple keyword matching
            query_terms = query.lower().split()
            results = []
            
            for tool in all_tools:
                score = 0.0
                tool_text = f"{tool['name']} {tool['description']} {' '.join(tool.get('tags', []))}".lower()
                
                # Count matching terms
                for term in query_terms:
                    if term in tool_text:
                        score += 1.0
                
                if score > 0:
                    # Normalize score
                    score = score / len(query_terms)
                    results.append({
                        "id": tool["id"],
                        "name": tool["name"],
                        "description": tool["description"],
                        "category": tool.get("category"),
                        "score": score,
                        "match_type": "keyword"
                    })
            
            # Sort by score and limit results
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    async def _hybrid_search(
        self,
        query: str,
        max_results: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            similarity_threshold: Similarity threshold
            
        Returns:
            List of search results
        """
        try:
            # Perform both search types
            semantic_results = await self._semantic_search(query, max_results, similarity_threshold)
            keyword_results = await self._keyword_search(query, max_results)
            
            # Combine and deduplicate results
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                combined_results[result["id"]] = {
                    **result,
                    "semantic_score": result["score"],
                    "keyword_score": 0.0
                }
            
            # Add keyword results
            for result in keyword_results:
                if result["id"] in combined_results:
                    # Update existing result
                    combined_results[result["id"]]["keyword_score"] = result["score"]
                    # Calculate combined score
                    combined_results[result["id"]]["score"] = (
                        combined_results[result["id"]]["semantic_score"] * 0.7 +
                        result["score"] * 0.3
                    )
                else:
                    combined_results[result["id"]] = {
                        **result,
                        "semantic_score": 0.0,
                        "keyword_score": result["score"],
                        "score": result["score"] * 0.3
                    }
            
            # Sort by combined score and limit results
            results = list(combined_results.values())
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def _calculate_similarity(self, query: str, tool: Dict[str, Any]) -> float:
        """
        Calculate similarity between query and tool.
        
        Args:
            query: Search query
            tool: Tool data
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Simple text-based similarity for now
            # In production, this would use vector embeddings
            
            query_lower = query.lower()
            tool_text = f"{tool['name']} {tool['description']} {' '.join(tool.get('tags', []))}".lower()
            
            # Calculate Jaccard similarity
            query_words = set(query_lower.split())
            tool_words = set(tool_text.split())
            
            if not query_words or not tool_words:
                return 0.0
            
            intersection = query_words.intersection(tool_words)
            union = query_words.union(tool_words)
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools for search.
        
        Returns:
            List of available tools
        """
        # This would integrate with the tool registry
        # For now, return mock data
        return [
            {
                "id": "tool-1",
                "name": "database_query",
                "description": "Query database with SQL",
                "category": "database",
                "tags": ["database", "sql", "query"]
            },
            {
                "id": "tool-2",
                "name": "api_client",
                "description": "Make HTTP API calls",
                "category": "api",
                "tags": ["http", "rest", "api"]
            },
            {
                "id": "tool-3",
                "name": "file_processor",
                "description": "Process files and documents",
                "category": "file",
                "tags": ["file", "io", "process"]
            }
        ]

    def _generate_search_id(self) -> str:
        """Generate a unique search ID."""
        import uuid
        return str(uuid.uuid4())

    def _update_search_metrics(self, duration: float, successful: bool) -> None:
        """
        Update search metrics.
        
        Args:
            duration: Search duration
            successful: Whether search was successful
        """
        self.search_metrics["total_searches"] += 1
        
        if successful:
            self.search_metrics["successful_searches"] += 1
        else:
            self.search_metrics["failed_searches"] += 1
        
        # Update average response time
        total_searches = self.search_metrics["total_searches"]
        current_avg = self.search_metrics["average_response_time"]
        
        if total_searches > 1:
            self.search_metrics["average_response_time"] = (
                (current_avg * (total_searches - 1) + duration) / total_searches
            )
        else:
            self.search_metrics["average_response_time"] = duration

    def get_search_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get search history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of search history entries
        """
        return self.search_history[-limit:]

    def get_search_metrics(self) -> Dict[str, Any]:
        """
        Get search metrics.
        
        Returns:
            Dictionary with search metrics
        """
        return self.search_metrics.copy()

    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get detailed search statistics.
        
        Returns:
            Dictionary with search statistics
        """
        successful_searches = [s for s in self.search_history if s.get("status") == "completed"]
        failed_searches = [s for s in self.search_history if s.get("status") == "failed"]
        
        # Calculate average response times by search type
        search_types = {}
        for search in successful_searches:
            search_type = search.get("search_type", "unknown")
            if search_type not in search_types:
                search_types[search_type] = {"count": 0, "total_time": 0.0}
            
            search_types[search_type]["count"] += 1
            search_types[search_type]["total_time"] += search.get("duration", 0.0)
        
        # Calculate averages
        for search_type in search_types:
            count = search_types[search_type]["count"]
            total_time = search_types[search_type]["total_time"]
            search_types[search_type]["average_time"] = total_time / count if count > 0 else 0.0
        
        return {
            "total_searches": len(self.search_history),
            "successful_searches": len(successful_searches),
            "failed_searches": len(failed_searches),
            "success_rate": len(successful_searches) / len(self.search_history) if self.search_history else 0.0,
            "average_response_time": self.search_metrics["average_response_time"],
            "search_types": search_types,
            "recent_queries": [s["query"] for s in self.search_history[-10:]]
        } 