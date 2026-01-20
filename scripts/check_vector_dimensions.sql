-- Check the current vector column dimensions in the database
-- Run this with: psql -U postgres -d staffing -f scripts/check_vector_dimensions.sql

-- Show vector column definition
SELECT
    column_name,
    data_type,
    udt_name,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'embeddings' AND column_name = 'vector';

-- Check pgvector version
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Count existing embeddings by dimension
SELECT
    dim,
    model,
    COUNT(*) as count
FROM embeddings
GROUP BY dim, model
ORDER BY dim, model;

-- Show sample embedding details
SELECT
    id,
    model,
    dim,
    array_length(string_to_array(replace(replace(vector::text, '[', ''), ']', ''), ','), 1) as actual_vector_length
FROM embeddings
LIMIT 5;
