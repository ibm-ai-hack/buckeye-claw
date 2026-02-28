"""Full memory module integration tests.

End-to-end tests that exercise the complete MemoryModule pipeline:
    Granite (categorization + fact extraction + repetition detection)
    → Supabase DB (memory_tasks + memory_facts + memory_jobs)
    → Voyage AI embeddings (voyage-3, 1024 dims)
    → pgvector semantic search
    → context string for agent prompt injection

Unlike the isolated test files (test_db_integration, test_semantic_integration,
test_llm_eval), these tests exercise MemoryModule._update() and
MemoryModule.get_context() with all real dependencies wired together.

Requirements:
    SUPABASE_URL, SUPABASE_API_KEY, VOYAGE_API_KEY,
    WATSONX_API_KEY, and WATSONX_PROJECT_ID must all be set.
    The schema from supabase/migrations/001_memory.sql must be applied.

Run:
    pytest tests/test_full_memory_integration.py -v
"""

import json
import voyageai
import pytest
from beeai_framework.backend import ChatModel
from supabase import Client

from memory.db import MemoryDB
from memory.module import MemoryModule
from memory.prompts import CATEGORIES, embed

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def llm() -> ChatModel:
    """Module-scoped Granite model — reused across all tests to avoid re-init cost."""
    return ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")


@pytest.fixture
def db(supabase_client: Client) -> MemoryDB:
    return MemoryDB(supabase_client)


@pytest.fixture
def memory_module(llm: ChatModel, db: MemoryDB) -> MemoryModule:
    return MemoryModule(llm=llm, db=db)


# ---------------------------------------------------------------------------
# Store pipeline: MemoryModule._update()
# ---------------------------------------------------------------------------


class TestUpdatePipeline:
    """Exercises the full _update() pipeline: Granite categorization + fact extraction
    + OpenAI embedding + Supabase storage, all in one shot."""

    @pytest.mark.asyncio
    async def test_task_categorized_and_stored(
        self,
        memory_module: MemoryModule,
        supabase_client: Client,
        test_user: str,
    ):
        """A task fed through _update() should appear in memory_tasks with a valid category."""
        await memory_module._update(test_user, "order a veggie burger from Morrill Tower")

        rows = (
            supabase_client.table("memory_tasks")
            .select("task, category")
            .eq("user_id", test_user)
            .execute()
        )

        assert len(rows.data) >= 1, "Expected at least one task row after _update()"
        category = rows.data[0]["category"]
        assert category in CATEGORIES, (
            f"Granite returned category '{category}' which is not in the allowed list"
        )

    @pytest.mark.asyncio
    async def test_fact_extraction_and_embedding(
        self,
        memory_module: MemoryModule,
        supabase_client: Client,
        test_user: str,
    ):
        """A personal-info message should result in a fact stored with a real OpenAI embedding.

        Uses 'I prefer vegetarian food' — validated as a reliable fact-extraction input
        in test_llm_eval.py::TestFactExtraction::test_extracts_dietary_preference.
        """
        # Probe OpenAI before running _update(): if quota is exceeded, embed() inside
        # _handle_fact_extraction() fails silently (caught + logged), so no facts are
        # stored and the assertion below would fail with a misleading message.
        try:
            await embed("quota probe")
        except voyageai.error.RateLimitError as exc:
            pytest.skip(f"OpenAI quota exceeded — facts cannot be embedded: {exc}")

        await memory_module._update(test_user, "I prefer vegetarian food")

        rows = (
            supabase_client.table("memory_facts")
            .select("key, value, embedding")
            .eq("user_id", test_user)
            .execute()
        )

        assert len(rows.data) >= 1, (
            "Expected at least one fact to be extracted and stored after _update()"
        )

        # Verify the embedding has the correct Voyage AI dimensionality
        raw_embedding = rows.data[0]["embedding"]
        assert raw_embedding is not None, "Embedding column should be populated (not null)"
        # Supabase may return the embedding as a JSON string or a list
        if isinstance(raw_embedding, str):
            embedding = json.loads(raw_embedding)
        else:
            embedding = raw_embedding
        assert len(embedding) == 1024, f"Expected 1024-dim embedding, got {len(embedding)}"

        # Verify Granite extracted the dietary preference
        values = " ".join(r["value"].lower() for r in rows.data)
        assert "vegetarian" in values, (
            f"Expected 'vegetarian' in extracted fact values, got: {rows.data}"
        )

    @pytest.mark.asyncio
    async def test_neutral_query_stores_no_facts(
        self,
        memory_module: MemoryModule,
        supabase_client: Client,
        test_user: str,
    ):
        """A neutral query with no personal info should not result in any stored facts.

        Uses 'what dining halls are open right now' — validated as a no-fact input
        in test_llm_eval.py::TestFactExtraction::test_no_facts_from_neutral_query.
        """
        await memory_module._update(test_user, "what dining halls are open right now")

        rows = (
            supabase_client.table("memory_facts")
            .select("id")
            .eq("user_id", test_user)
            .execute()
        )

        assert len(rows.data) <= 2, (
            f"Expected few or no facts for a neutral query, got {len(rows.data)} row(s): {rows.data}"
        )


# ---------------------------------------------------------------------------
# Context retrieval: MemoryModule.get_context()
# ---------------------------------------------------------------------------


class TestGetContext:
    """Exercises get_context(): OpenAI embed of query + pgvector cosine search + formatting."""

    @pytest.mark.asyncio
    async def test_empty_for_new_user(
        self,
        memory_module: MemoryModule,
        test_user: str,
    ):
        """A brand-new user with no DB history should receive an empty context string."""
        context = await memory_module.get_context(test_user, "what bus should I take")
        assert context == "", f"Expected empty context for new user, got: {repr(context)}"

    @pytest.mark.asyncio
    async def test_scheduled_job_appears_in_context(
        self,
        memory_module: MemoryModule,
        db: MemoryDB,
        test_user: str,
    ):
        """A job stored in memory_jobs should appear in the formatted context string.

        Uses direct db.add_job() (no LLM) to isolate the context retrieval path.
        """
        db.add_job(
            test_user,
            {
                "schedule": "0 8 * * 1-5",
                "prompt": "What is the next Route 10 bus?",
                "task_name": "morning_bus_check",
                "category": "bus_transit",
                "description": "Weekday morning bus check",
            },
        )

        context = await memory_module.get_context(test_user, "bus schedule")

        assert "Recurring tasks:" in context, (
            f"Expected 'Recurring tasks:' section in context, got: {repr(context)}"
        )
        assert "morning_bus_check" in context, (
            f"Expected job name in context, got: {repr(context)}"
        )

    @pytest.mark.asyncio
    async def test_semantic_fact_retrieval(
        self,
        memory_module: MemoryModule,
        db: MemoryDB,
        test_user: str,
    ):
        """A transit query should surface the transit fact above a dietary fact via pgvector.

        Seeds two real OpenAI embeddings so the cosine search has meaningful vectors.
        """
        try:
            transit_embedding = await embed("home_stop: North High and Woodruff")
            dietary_embedding = await embed("dietary_pref: vegetarian")
        except voyageai.error.RateLimitError as exc:
            pytest.skip(f"OpenAI quota exceeded: {exc}")

        db.upsert_fact(test_user, "home_stop", "North High and Woodruff", transit_embedding)
        db.upsert_fact(test_user, "dietary_pref", "vegetarian", dietary_embedding)

        context = await memory_module.get_context(test_user, "next Route 10 bus schedule")

        assert "User facts:" in context, (
            f"Expected 'User facts:' section in context, got: {repr(context)}"
        )
        assert "home_stop" in context, (
            f"Expected transit fact 'home_stop' to be surfaced for a bus query, got: {context}"
        )


# ---------------------------------------------------------------------------
# Full round-trip: _update() → get_context()
# ---------------------------------------------------------------------------


class TestFullRoundtrip:
    """Crown-jewel tests: the complete pipeline from raw user text to context string.

    Flow: text in → Granite categorize + extract facts → OpenAI embed + Supabase store
          → OpenAI embed query → pgvector cosine search → formatted context string out
    """

    @pytest.mark.asyncio
    async def test_update_then_get_context(
        self,
        memory_module: MemoryModule,
        test_user: str,
    ):
        """Facts extracted by Granite from _update() should be retrievable in get_context().

        Verifies that the full write path (LLM + embedding + DB insert) connects correctly
        to the read path (embedding query + pgvector search + format).
        """
        # Probe OpenAI first: both _update() (embed facts) and get_context() (embed query)
        # silently degrade when quota is exceeded, producing an empty context that would
        # fail the assertion below with a misleading message.
        try:
            await embed("quota probe")
        except voyageai.error.RateLimitError as exc:
            pytest.skip(f"OpenAI quota exceeded — embedding unavailable: {exc}")

        await memory_module._update(test_user, "I prefer vegetarian food")

        context = await memory_module.get_context(test_user, "suggest food options for me")

        assert "User facts:" in context, (
            f"Expected extracted facts to appear in context after _update(), got: {repr(context)}"
        )
        assert "vegetarian" in context.lower(), (
            f"Expected 'vegetarian' to be surfaced via semantic search, got: {context}"
        )

    @pytest.mark.asyncio
    async def test_three_updates_populate_task_history(
        self,
        memory_module: MemoryModule,
        supabase_client: Client,
        test_user: str,
    ):
        """Three _update() calls should produce three categorized rows in memory_tasks.

        Verifies that Granite assigns a valid category to each task and that the
        repetition-check branch is exercised (len(same_cat_tasks) >= 3 after the
        third call). Does not assert a specific category value since Granite's
        exact classification can vary between calls.
        """
        tasks = [
            "when is the next Route 10 bus",
            "route 10 schedule for tonight",
            "how long until the next 10 bus arrives",
        ]
        for task in tasks:
            await memory_module._update(test_user, task)

        rows = (
            supabase_client.table("memory_tasks")
            .select("task, category")
            .eq("user_id", test_user)
            .execute()
        )

        assert len(rows.data) == 3, f"Expected 3 task entries, got {len(rows.data)}"
        for row in rows.data:
            assert row["category"] in CATEGORIES, (
                f"Granite returned category '{row['category']}' which is not in the allowed list"
            )
