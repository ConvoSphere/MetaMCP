"""
LLM Service Module

This module provides LLM integration for embeddings generation,
text generation, and tool description processing.
"""

import asyncio
from typing import Dict, List, Optional, Any
import httpx

from ..config import get_settings, LLMProvider
from ..exceptions import EmbeddingError
from ..utils.logging import get_logger


logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    """
    LLM Service for embeddings and text generation.
    
    This class provides integration with various LLM providers
    for generating embeddings and processing text.
    """
    
    def __init__(self, settings):
        """
        Initialize LLM Service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.provider = settings.llm_provider
        
        # Provider-specific clients
        self.openai_client = None
        self.ollama_client = None
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30)
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the LLM service."""
        if self._initialized:
            return
            
        try:
            logger.info(f"Initializing LLM Service with provider: {self.provider}")
            
            if self.provider == LLMProvider.OPENAI:
                await self._initialize_openai()
            elif self.provider == LLMProvider.OLLAMA:
                await self._initialize_ollama()
            else:
                logger.warning(f"Unsupported LLM provider: {self.provider}")
            
            self._initialized = True
            logger.info("LLM Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {e}")
            raise EmbeddingError(
                message=f"Failed to initialize LLM service: {str(e)}",
                error_code="llm_init_failed"
            )
    
    async def _initialize_openai(self) -> None:
        """Initialize OpenAI client."""
        try:
            import openai
            
            if not self.settings.openai_api_key:
                raise EmbeddingError(
                    message="OpenAI API key not configured",
                    error_code="missing_api_key"
                )
            
            self.openai_client = openai.AsyncOpenAI(
                api_key=self.settings.openai_api_key.get_secret_value(),
                base_url=self.settings.azure_openai_endpoint if self.settings.azure_openai_endpoint else None
            )
            
            logger.info("OpenAI client initialized")
            
        except ImportError:
            raise EmbeddingError(
                message="OpenAI library not installed",
                error_code="missing_dependency"
            )
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to initialize OpenAI client: {str(e)}",
                error_code="openai_init_failed"
            )
    
    async def _initialize_ollama(self) -> None:
        """Initialize Ollama client."""
        try:
            import ollama
            
            # Test connection to Ollama
            response = await self.http_client.get(f"{self.settings.ollama_base_url}/api/tags")
            if response.status_code != 200:
                raise EmbeddingError(
                    message="Ollama server not accessible",
                    error_code="ollama_unavailable"
                )
            
            self.ollama_client = ollama
            logger.info("Ollama client initialized")
            
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to initialize Ollama client: {str(e)}",
                error_code="ollama_init_failed"
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            List of embedding values
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            if not self._initialized:
                raise EmbeddingError(
                    message="LLM service not initialized",
                    error_code="service_not_initialized"
                )
            
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai_embedding(text)
            elif self.provider == LLMProvider.OLLAMA:
                return await self._generate_ollama_embedding(text)
            else:
                # Fallback to simple hash-based embedding
                return self._generate_fallback_embedding(text)
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(
                message=f"Failed to generate embedding: {str(e)}",
                error_code="embedding_generation_failed"
            )
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        try:
            response = await self.openai_client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise EmbeddingError(
                message=f"OpenAI embedding failed: {str(e)}",
                error_code="openai_embedding_failed"
            )
    
    async def _generate_ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        try:
            response = await self.http_client.post(
                f"{self.settings.ollama_base_url}/api/embeddings",
                json={
                    "model": self.settings.ollama_embedding_model,
                    "prompt": text
                }
            )
            
            if response.status_code != 200:
                raise EmbeddingError(
                    message=f"Ollama embedding failed: {response.text}",
                    error_code="ollama_embedding_failed"
                )
            
            data = response.json()
            return data.get("embedding", [])
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise EmbeddingError(
                message=f"Ollama embedding failed: {str(e)}",
                error_code="ollama_embedding_failed"
            )
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback embedding using hash."""
        import hashlib
        
        # Create hash-based embedding
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float values between 0 and 1
        embedding = [float(b) / 255.0 for b in hash_bytes]
        
        # Pad or truncate to standard size
        target_size = self.settings.vector_dimension
        if len(embedding) < target_size:
            # Pad with zeros
            embedding.extend([0.0] * (target_size - len(embedding)))
        else:
            # Truncate
            embedding = embedding[:target_size]
        
        return embedding
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate text using LLM.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            EmbeddingError: If text generation fails
        """
        try:
            if not self._initialized:
                raise EmbeddingError(
                    message="LLM service not initialized",
                    error_code="service_not_initialized"
                )
            
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai_text(prompt, max_tokens)
            elif self.provider == LLMProvider.OLLAMA:
                return await self._generate_ollama_text(prompt, max_tokens)
            else:
                raise EmbeddingError(
                    message=f"Text generation not supported for provider: {self.provider}",
                    error_code="unsupported_provider"
                )
                
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise EmbeddingError(
                message=f"Failed to generate text: {str(e)}",
                error_code="text_generation_failed"
            )
    
    async def _generate_openai_text(self, prompt: str, max_tokens: int) -> str:
        """Generate text using OpenAI."""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            raise EmbeddingError(
                message=f"OpenAI text generation failed: {str(e)}",
                error_code="openai_text_failed"
            )
    
    async def _generate_ollama_text(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Ollama."""
        try:
            response = await self.http_client.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
            )
            
            if response.status_code != 200:
                raise EmbeddingError(
                    message=f"Ollama text generation failed: {response.text}",
                    error_code="ollama_text_failed"
                )
            
            data = response.json()
            return data.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            raise EmbeddingError(
                message=f"Ollama text generation failed: {str(e)}",
                error_code="ollama_text_failed"
            )
    
    async def shutdown(self) -> None:
        """Shutdown the LLM service."""
        if not self._initialized:
            return
            
        logger.info("Shutting down LLM Service...")
        
        # Close HTTP client
        await self.http_client.aclose()
        
        self._initialized = False
        logger.info("LLM Service shutdown complete")
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized 