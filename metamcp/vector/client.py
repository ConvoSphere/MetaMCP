"""
Vector Search Client

This module provides vector search functionality using Weaviate.
It handles embeddings storage, search, and similarity calculations.
"""

from typing import Any

import weaviate
from weaviate import WeaviateClient

from ..config import get_settings
from ..exceptions import VectorSearchError
from ..utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorSearchClient:
    """
    Vector Search Client using Weaviate.
    
    This class provides vector search functionality for semantic
    tool discovery and similarity matching.
    """

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        timeout: int = 30
    ):
        """
        Initialize Vector Search Client.
        
        Args:
            url: Weaviate server URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.url = url
        self.api_key = api_key
        self.timeout = timeout

        # Weaviate client
        self.client: weaviate.WeaviateClient | None = None

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the vector search client."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Vector Search Client...")

            # Create Weaviate client using v4 API
            from weaviate.classes.config import ConnectionParams
            
            if self.api_key:
                connection_params = ConnectionParams.from_url(
                    self.url,
                    auth_credentials=weaviate.auth.Auth.api_key(self.api_key),
                    additional_headers={"X-OpenAI-Api-Key": self.api_key}
                )
            else:
                connection_params = ConnectionParams.from_url(self.url)
                
            self.client = weaviate.WeaviateClient(connection_params)

            # Test connection
            await self._test_connection()

            # Initialize collections
            await self._initialize_collections()

            self._initialized = True
            logger.info("Vector Search Client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Vector Search Client: {e}")
            raise VectorSearchError(
                message=f"Failed to initialize vector search client: {str(e)}",
                error_code="vector_init_failed"
            ) from e

    async def _test_connection(self) -> None:
        """Test connection to Weaviate."""
        try:
            # Simple health check using v4 API
            response = self.client.get_meta()
            logger.info("Weaviate connection test successful")
        except Exception as e:
            logger.error(f"Weaviate connection test failed: {e}")
            raise VectorSearchError(
                message=f"Weaviate connection failed: {str(e)}",
                error_code="connection_failed"
            ) from e

    async def _initialize_collections(self) -> None:
        """Initialize required collections."""
        try:
            # Create tools collection if it doesn't exist
            if not self.client.collections.exists("tools"):
                self.client.collections.create(
                    name="tools",
                    vectorizer_config=weaviate.config.Configure.Vectorizer.none(),
                    properties=[
                        weaviate.config.Property(name="name", data_type=weaviate.config.DataType.TEXT),
                        weaviate.config.Property(name="description", data_type=weaviate.config.DataType.TEXT),
                        weaviate.config.Property(name="categories", data_type=weaviate.config.DataType.TEXT_ARRAY),
                        weaviate.config.Property(name="endpoint", data_type=weaviate.config.DataType.TEXT),
                        weaviate.config.Property(name="security_level", data_type=weaviate.config.DataType.TEXT),
                        weaviate.config.Property(name="registered_at", data_type=weaviate.config.DataType.DATE),
                        weaviate.config.Property(name="status", data_type=weaviate.config.DataType.TEXT)
                    ]
                )
                logger.info("Created tools collection")
            else:
                logger.info("Tools collection already exists")

        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise VectorSearchError(
                message=f"Failed to initialize collections: {str(e)}",
                error_code="collection_init_failed"
            ) from e

    async def store_embedding(
        self,
        collection: str,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any]
    ) -> None:
        """
        Store an embedding with metadata.
        
        Args:
            collection: Collection name
            id: Unique identifier
            embedding: Vector embedding
            metadata: Associated metadata
        """
        try:
            if not self.client:
                raise VectorSearchError(
                    message="Vector client not initialized",
                    error_code="client_not_initialized"
                )

            # Prepare data object
            data_object = {
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "categories": metadata.get("categories", []),
                "endpoint": metadata.get("endpoint", ""),
                "security_level": metadata.get("security_level", "low"),
                "registered_at": metadata.get("registered_at", ""),
                "status": metadata.get("status", "active")
            }

            # Store in Weaviate
            self.client.collections.get(collection).data.insert(
                data_object=data_object,
                uuid=id,
                vector=embedding
            )

            logger.info(f"Stored embedding for {id} in collection {collection}")

        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            raise VectorSearchError(
                message=f"Failed to store embedding: {str(e)}",
                error_code="store_failed"
            ) from e

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            collection: Collection name
            query_embedding: Query vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of search results with metadata
        """
        try:
            if not self.client:
                raise VectorSearchError(
                    message="Vector client not initialized",
                    error_code="client_not_initialized"
                )

            # Perform vector search
            response = self.client.collections.get(collection).query.near_vector(
                near_vector=query_embedding,
                limit=limit,
                return_properties=["name", "description", "categories", "endpoint", "security_level", "status"]
            )

            # Process results
            results = []
            for obj in response.objects:
                if obj.score >= similarity_threshold:
                    results.append({
                        "id": obj.uuid,
                        "score": obj.score,
                        "metadata": {
                            "name": obj.properties.get("name", ""),
                            "description": obj.properties.get("description", ""),
                            "categories": obj.properties.get("categories", []),
                            "endpoint": obj.properties.get("endpoint", ""),
                            "security_level": obj.properties.get("security_level", "low"),
                            "status": obj.properties.get("status", "active")
                        }
                    })

            logger.info(f"Found {len(results)} results for vector search")
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorSearchError(
                message=f"Vector search failed: {str(e)}",
                error_code="search_failed"
            ) from e

    async def delete_embedding(self, collection: str, id: str) -> None:
        """
        Delete an embedding by ID.
        
        Args:
            collection: Collection name
            id: Unique identifier
        """
        try:
            if not self.client:
                raise VectorSearchError(
                    message="Vector client not initialized",
                    error_code="client_not_initialized"
                )

            self.client.collections.get(collection).data.delete_by_id(id)
            logger.info(f"Deleted embedding {id} from collection {collection}")

        except Exception as e:
            logger.error(f"Failed to delete embedding: {e}")
            raise VectorSearchError(
                message=f"Failed to delete embedding: {str(e)}",
                error_code="delete_failed"
            ) from e

    async def shutdown(self) -> None:
        """Shutdown the vector search client."""
        if not self._initialized:
            return

        logger.info("Shutting down Vector Search Client...")

        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.error(f"Error closing Weaviate client: {e}")

        self._initialized = False
        logger.info("Vector Search Client shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized
