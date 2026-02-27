-- BuckeyeBot Memory System Schema
-- Run this in your Supabase SQL editor or via Supabase CLI migrations

-- Enable pgvector extension (required for fact embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Profiles
-- Standalone user table. Linked to Supabase Auth (auth.users)
-- when a user creates a web dashboard account; bot creates
-- entries from phone number alone.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone      TEXT UNIQUE NOT NULL,   -- E.164 format, e.g. +16141234567
    email      TEXT,                   -- populated when user signs up on web
    auth_id    UUID UNIQUE,            -- references auth.users(id) once linked
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Store 1: Scheduled / recurring jobs
-- Detected by Granite when a task pattern repeats over time.
-- Jobs are eventually consumed by a scheduler that sends the
-- NL prompt to the agent at the specified cron time.
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_jobs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    schedule         TEXT NOT NULL,        -- cron expression, e.g. "0 8 * * 1-5"
    prompt           TEXT NOT NULL,        -- NL sent to agent when job fires
    task_name        TEXT NOT NULL,        -- slug identifier, e.g. "check_bus_route_10"
    description      TEXT,
    category         TEXT NOT NULL,        -- same category system as memory_tasks
    occurrence_count INT  NOT NULL DEFAULT 1,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memory_jobs_user_id_idx ON memory_jobs(user_id);

-- ============================================================
-- Store 2: Recent task history (30-day rolling window)
-- Each task is categorized by Granite at write time, enabling
-- efficient category-scoped repetition detection.
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_tasks (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    task       TEXT NOT NULL,              -- raw user message / task description
    category   TEXT NOT NULL,              -- e.g. "bus_transit", "food_ordering"
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memory_tasks_user_category_idx
    ON memory_tasks(user_id, category, created_at DESC);

-- ============================================================
-- Store 3: User facts with pgvector embeddings
-- text-embedding-3-small produces 1536-dimensional vectors.
-- Semantic retrieval: top-K relevant facts per query.
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_facts (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    key        TEXT NOT NULL,
    value      TEXT NOT NULL,
    embedding  VECTOR(1536),               -- text-embedding-3-small
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, key)
);

-- ivfflat index for approximate nearest-neighbor cosine search
-- Requires at least ~100 rows before it becomes useful.
-- Use exact scan (no index) for smaller tables; Postgres auto-selects.
CREATE INDEX IF NOT EXISTS memory_facts_embedding_idx
    ON memory_facts USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS memory_facts_user_id_idx ON memory_facts(user_id);

-- ============================================================
-- RPC: match_facts
-- Called by the Python backend to retrieve the top-K most
-- semantically relevant user facts for a given query embedding.
-- ============================================================
CREATE OR REPLACE FUNCTION match_facts(
    query_embedding VECTOR(1536),
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
