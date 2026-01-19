#!/usr/bin/env python3
"""
Add vector index to embeddings table based on embedding dimensions.

This script checks the configured embedding model dimensions and creates
an appropriate vector index if dimensions are ≤2000 (pgvector limit).
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text
from app.core.database import engine
from app.services.embeddings import get_embeddings_service


def add_vector_index():
    """Add vector index if embedding dimensions are within pgvector limits"""

    # Get embedding service to check dimensions
    embeddings_service = get_embeddings_service()
    dimension = embeddings_service.get_dimension()

    print(f"Embedding model: {embeddings_service.model}")
    print(f"Embedding dimensions: {dimension}")

    if dimension > 2000:
        print("\n⚠️  WARNING: Embedding dimensions exceed pgvector index limit (2000)")
        print(f"   Your model produces {dimension}-dimensional vectors.")
        print("\n   Options:")
        print("   1. Continue without index (slower for large datasets)")
        print("   2. Switch to a smaller model like text-embedding-3-small (1536 dims)")
        print("\n   The system will work without an index using sequential scans.")
        return 1

    print(f"\n✓ Dimensions are within limit ({dimension} ≤ 2000)")
    print("  Creating HNSW index for optimal performance...")

    try:
        with engine.connect() as conn:
            # Check if index already exists
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'embeddings'
                AND indexname IN ('idx_embeddings_hnsw', 'idx_embeddings_ivfflat')
            """))
            existing = result.fetchone()

            if existing:
                print(f"\n✓ Vector index '{existing[0]}' already exists. Skipping creation.")
                return 0

            # Create HNSW index (best for most use cases when dims ≤ 2000)
            print("  Creating index (this may take a while for large datasets)...")
            conn.execute(text(
                "CREATE INDEX idx_embeddings_hnsw ON embeddings "
                "USING hnsw (vector vector_cosine_ops)"
            ))
            conn.commit()

            print("\n✓ Successfully created HNSW index on embeddings.vector")
            print("  Vector similarity searches will now be much faster!")
            return 0

    except Exception as e:
        print(f"\n✗ Error creating index: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(add_vector_index())
