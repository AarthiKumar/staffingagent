"""Embeddings service with pluggable providers"""
import hashlib
from typing import List, Optional

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingsService:
    """Generate embeddings with provider selection"""

    def __init__(self, model: str, provider: str = "local"):
        self.model = model
        self.provider = provider
        self._encoder = None
        self._openai_client = None

        if provider == "local":
            self._init_local_encoder()
        elif provider == "openai":
            self._init_openai_client()

    def _init_local_encoder(self):
        """Initialize local sentence-transformers encoder"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading local embeddings model: {self.model}")
            # Explicitly set device to 'cpu' to avoid PyTorch meta tensor issues
            # trust_remote_code=True allows loading newer model architectures
            self._encoder = SentenceTransformer(
                self.model,
                device='cpu',
                trust_remote_code=True
            )
            logger.info(f"Model loaded successfully, dimension: {self._encoder.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embeddings model: {e}")
            raise

    def _init_openai_client(self):
        """Initialize OpenAI client"""
        if not settings.llm_api_key:
            raise ValueError("OpenAI API key not configured. Set LLM_API_KEY in .env")

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.llm_api_key)
            logger.info(f"OpenAI embeddings initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def embed_texts(self, texts: List[str], agent_id: str) -> List[np.ndarray]:
        """Generate embeddings for list of texts"""
        if not texts:
            return []

        if self.provider == "local":
            return self._embed_local(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _embed_local(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using local model"""
        if self._encoder is None:
            raise RuntimeError("Encoder not initialized")

        try:
            embeddings = self._encoder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [emb for emb in embeddings]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def _embed_openai(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using OpenAI API"""
        if self._openai_client is None:
            raise RuntimeError("OpenAI client not initialized")

        try:
            # OpenAI embeddings API supports batch processing
            response = self._openai_client.embeddings.create(
                model=self.model,
                input=texts
            )

            # Extract embeddings and convert to numpy arrays
            embeddings = [np.array(item.embedding, dtype=np.float32) for item in response.data]

            logger.info(f"Generated {len(embeddings)} OpenAI embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise

    def embed_single(self, text: str, agent_id: str) -> np.ndarray:
        """Generate embedding for single text"""
        results = self.embed_texts([text], agent_id)
        return results[0] if results else np.array([])

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self.provider == "local" and self._encoder:
            return self._encoder.get_sentence_embedding_dimension()
        elif self.provider == "openai":
            # OpenAI embedding dimensions by model
            dimensions = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536,
            }
            return dimensions.get(self.model, 1536)
        return 384  # Default for small local models

    def compute_hash(self, text: str) -> str:
        """Compute cache hash for text"""
        combined = f"{self.model}:{text}"
        return hashlib.sha256(combined.encode()).hexdigest()


def get_embeddings_service() -> EmbeddingsService:
    """Get configured embeddings service"""
    return EmbeddingsService(
        model=settings.embeddings_model,
        provider=settings.embeddings_provider,
    )
