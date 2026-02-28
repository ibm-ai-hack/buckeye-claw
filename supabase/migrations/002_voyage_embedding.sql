-- Migrate fact embeddings from OpenAI text-embedding-3-small (1536 dims)
--                           to Voyage AI voyage-3 (1024 dims)
--
-- Run this in your Supabase SQL editor after 001_memory.sql.
-- NOTE: This alters the embedding column type. Any existing rows in
-- memory_facts will need to be re-embedded (their stored vectors are
-- incompatible with the new dimension). In production, truncate
-- memory_facts and re-populate via the memory module before deploying.

-- Step 1: Drop the ivfflat index (cannot change column type with index present)
DROP INDEX IF EXISTS memory_facts_embedding_idx;

-- Step 2: Change the embedding column from 1536 → 1024 dimensions
ALTER TABLE memory_facts
    ALTER COLUMN embedding TYPE VECTOR(1024);

-- Step 3: Recreate the ivfflat index for the new dimensionality
CREATE INDEX memory_facts_embedding_idx
    ON memory_facts USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Step 4: Replace the match_facts RPC with the updated vector signature
CREATE OR REPLACE FUNCTION match_facts(
    query_embedding VECTOR(1024),
    p_user_id       UUID,
    match_count     INT DEFAULT 5
)
RETURNS TABLE(key TEXT, value TEXT, similarity FLOAT)
LANGUAGE SQL STABLE
AS $$
    SELECT
        key,
        value,
        1 - (embedding <=> query_embedding) AS similarity
    FROM memory_facts
    WHERE user_id = p_user_id
      AND embedding IS NOT NULL
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
