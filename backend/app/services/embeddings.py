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

        if provider == "local":
            self._init_local_encoder()

    def _init_local_encoder(self):
        """Initialize local sentence-transformers encoder"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading local embeddings model: {self.model}")
            self._encoder = SentenceTransformer(self.model)
            logger.info(f"Model loaded successfully, dimension: {self._encoder.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embeddings model: {e}")
            raise

    def embed_texts(self, texts: List[str], agent_id: str) -> List[np.ndarray]:
        """Generate embeddings for list of texts"""
        if not texts:
            return []

        if self.provider == "local":
            return self._embed_local(texts)
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

    def embed_single(self, text: str, agent_id: str) -> np.ndarray:
        """Generate embedding for single text"""
        results = self.embed_texts([text], agent_id)
        return results[0] if results else np.array([])

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self.provider == "local" and self._encoder:
            return self._encoder.get_sentence_embedding_dimension()
        return 384  # Default for small models

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
