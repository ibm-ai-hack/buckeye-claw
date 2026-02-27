"""Semantic integration tests: real OpenAI embeddings + Supabase pgvector.

These tests verify that the cosine similarity ranking in `match_facts` actually
reflects semantic relevance — e.g. a bus-related query ranks transit facts above
dietary facts, and vice versa for a food-related query.

Requirements:
    SUPABASE_URL, SUPABASE_API_KEY, and OPENAI_API_KEY must be set.
    The schema from supabase/migrations/001_memory.sql must be applied.

Run:
    pytest tests/test_semantic_integration.py -v
"""

import pytest
from supabase import Client

from memory.db import MemoryDB
from memory.prompts import embed

pytestmark = pytest.mark.semantic


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(supabase_client: Client) -> MemoryDB:
    return MemoryDB(supabase_client)


# ---------------------------------------------------------------------------
# pgvector cosine ranking
# ---------------------------------------------------------------------------

class TestPgvectorRanking:
    @pytest.mark.asyncio
    async def test_bus_query_ranks_transit_fact_higher(
        self, db: MemoryDB, supabase_client: Client, test_user: str
    ):
        """A bus-related query should rank the transit fact above the dietary fact."""
        transit_embedding = await embed("home_stop: North High and Woodruff")
        dietary_embedding = await embed("dietary_pref: vegetarian")

        db.upsert_fact(test_user, "home_stop", "North High and Woodruff", transit_embedding)
        db.upsert_fact(test_user, "dietary_pref", "vegetarian", dietary_embedding)

        query_embedding = await embed("next Route 10 bus schedule")
        results = db.get_relevant_facts(test_user, query_embedding, k=5)

        # Build a similarity lookup by key
        similarity = {r["key"]: r["similarity"] for r in results}
        assert "home_stop" in similarity, "home_stop fact not returned"
        assert "dietary_pref" in similarity, "dietary_pref fact not returned"
        assert similarity["home_stop"] > similarity["dietary_pref"], (
            f"Expected home_stop ({similarity['home_stop']:.4f}) to rank higher than "
            f"dietary_pref ({similarity['dietary_pref']:.4f}) for a bus query"
        )

    @pytest.mark.asyncio
    async def test_food_query_ranks_dietary_fact_higher(
        self, db: MemoryDB, supabase_client: Client, test_user: str
    ):
        """A food-related query should rank the dietary fact above the transit fact."""
        transit_embedding = await embed("home_stop: North High and Woodruff")
        dietary_embedding = await embed("dietary_pref: vegetarian")

        db.upsert_fact(test_user, "home_stop", "North High and Woodruff", transit_embedding)
        db.upsert_fact(test_user, "dietary_pref", "vegetarian", dietary_embedding)

        query_embedding = await embed("vegetarian food options on campus")
        results = db.get_relevant_facts(test_user, query_embedding, k=5)

        similarity = {r["key"]: r["similarity"] for r in results}
        assert "home_stop" in similarity
        assert "dietary_pref" in similarity
        assert similarity["dietary_pref"] > similarity["home_stop"], (
            f"Expected dietary_pref ({similarity['dietary_pref']:.4f}) to rank higher than "
            f"home_stop ({similarity['home_stop']:.4f}) for a food query"
        )


class TestEmbeddingStorage:
    @pytest.mark.asyncio
    async def test_embedding_column_is_populated(
        self, db: MemoryDB, supabase_client: Client, test_user: str
    ):
        """After upsert_fact(), the embedding column in the DB should be non-null with 1536 dims."""
        embedding = await embed("major: Computer Science and Engineering")
        db.upsert_fact(test_user, "major", "Computer Science and Engineering", embedding)

        row = (
            supabase_client.table("memory_facts")
            .select("embedding")
            .eq("user_id", test_user)
            .eq("key", "major")
            .maybe_single()
            .execute()
        )

        stored = row.data["embedding"]
        assert stored is not None, "embedding column should not be null"
        assert len(stored) == 1536, f"Expected 1536 dims, got {len(stored)}"

    @pytest.mark.asyncio
    async def test_k_limit_respected(
        self, db: MemoryDB, test_user: str
    ):
        """get_relevant_facts(k=2) should return at most 2 rows even when more exist."""
        facts = [
            ("home_stop", "North High and Woodruff"),
            ("dietary_pref", "vegetarian"),
            ("major", "CSE"),
            ("dorm", "Scott House"),
        ]
        for key, value in facts:
            embedding = await embed(f"{key}: {value}")
            db.upsert_fact(test_user, key, value, embedding)

        query_embedding = await embed("student preferences")
        results = db.get_relevant_facts(test_user, query_embedding, k=2)

        assert len(results) == 2, f"Expected 2 results for k=2, got {len(results)}"
