-- Initialize pgvector extension and create HNSW index
CREATE EXTENSION IF NOT EXISTS vector;

-- Create HNSW index on embeddings vector column
-- This index will be created after the embeddings table is created by Alembic
-- Uncomment the following line after running migrations:
-- CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw ON embeddings USING hnsw (vector vector_cosine_ops);
