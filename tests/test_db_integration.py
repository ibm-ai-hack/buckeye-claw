"""Real-database integration tests for the memory module.

These tests execute against a live Supabase project and verify that the
actual SQL (inserts, upserts, deletes, RPC calls) behaves as expected.

Requirements:
    SUPABASE_URL and SUPABASE_API_KEY must be set (see .env.example).
    The schema from supabase/migrations/001_memory.sql must be applied.

Run:
    pytest tests/test_db_integration.py -v
"""

from datetime import datetime, timedelta, timezone

import pytest
from supabase import Client

from memory.db import MemoryDB

pytestmark = pytest.mark.integration

_DUMMY_EMBEDDING = [0.0] * 1024  # valid dimension, not semantically meaningful


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(supabase_client: Client) -> MemoryDB:
    return MemoryDB(supabase_client)


# ---------------------------------------------------------------------------
# Store 2 — Tasks
# ---------------------------------------------------------------------------

class TestPushTaskIntegration:
    def test_push_task_persists(self, db: MemoryDB, supabase_client: Client, test_user: str):
        """A pushed task should be retrievable from the database."""
        db.push_task(test_user, "next Route 10 bus", "bus_transit")

        rows = (
            supabase_client.table("memory_tasks")
            .select("task, category")
            .eq("user_id", test_user)
            .execute()
        )
        tasks = [r["task"] for r in rows.data]
        assert "next Route 10 bus" in tasks

    def test_get_tasks_by_category_filters_correctly(
        self, db: MemoryDB, test_user: str
    ):
        """Tasks from other categories should not appear in a category-scoped query."""
        db.push_task(test_user, "next 10 bus", "bus_transit")
        db.push_task(test_user, "order sandwich", "food_ordering")

        bus_tasks = db.get_tasks_by_category(test_user, "bus_transit")
        food_tasks = db.get_tasks_by_category(test_user, "food_ordering")

        assert "next 10 bus" in bus_tasks
        assert "order sandwich" not in bus_tasks
        assert "order sandwich" in food_tasks
        assert "next 10 bus" not in food_tasks

    def test_push_task_30_day_pruning(
        self, db: MemoryDB, supabase_client: Client, test_user: str
    ):
        """Tasks older than 30 days should be pruned when a new task is pushed."""
        old_date = (
            datetime.now(tz=timezone.utc) - timedelta(days=31)
        ).isoformat()

        # Insert a backdated row directly (bypasses push_task pruning trigger)
        supabase_client.table("memory_tasks").insert(
            {
                "user_id": test_user,
                "task": "stale bus task",
                "category": "bus_transit",
                "created_at": old_date,
            }
        ).execute()

        # Verify it's there before pruning
        pre_rows = (
            supabase_client.table("memory_tasks")
            .select("task")
            .eq("user_id", test_user)
            .execute()
        )
        assert any(r["task"] == "stale bus task" for r in pre_rows.data)

        # Push a fresh task — triggers the 30-day DELETE
        db.push_task(test_user, "fresh bus task", "bus_transit")

        post_rows = (
            supabase_client.table("memory_tasks")
            .select("task")
            .eq("user_id", test_user)
            .execute()
        )
        tasks = [r["task"] for r in post_rows.data]

        assert "stale bus task" not in tasks, "30-day-old task should have been pruned"
        assert "fresh bus task" in tasks


# ---------------------------------------------------------------------------
# Store 3 — Facts + pgvector
# ---------------------------------------------------------------------------

class TestUpsertFactIntegration:
    def test_upsert_fact_no_duplicate(
        self, db: MemoryDB, supabase_client: Client, test_user: str
    ):
        """Upserting the same key twice should produce exactly one row."""
        db.upsert_fact(test_user, "dietary_pref", "vegetarian", _DUMMY_EMBEDDING)
        db.upsert_fact(test_user, "dietary_pref", "vegan", _DUMMY_EMBEDDING)

        rows = (
            supabase_client.table("memory_facts")
            .select("id")
            .eq("user_id", test_user)
            .eq("key", "dietary_pref")
            .execute()
        )
        assert len(rows.data) == 1, "Expected exactly 1 row after two upserts with the same key"

    def test_upsert_fact_updates_value(
        self, db: MemoryDB, supabase_client: Client, test_user: str
    ):
        """The second upsert should overwrite the value, not duplicate it."""
        db.upsert_fact(test_user, "dietary_pref", "vegetarian", _DUMMY_EMBEDDING)
        db.upsert_fact(test_user, "dietary_pref", "vegan", _DUMMY_EMBEDDING)

        row = (
            supabase_client.table("memory_facts")
            .select("value")
            .eq("user_id", test_user)
            .eq("key", "dietary_pref")
            .maybe_single()
            .execute()
        )
        assert row.data["value"] == "vegan", "Second upsert should have updated the value"

    def test_get_relevant_facts_rpc_returns_rows(
        self, db: MemoryDB, test_user: str
    ):
        """The match_facts RPC should execute and return the upserted fact."""
        db.upsert_fact(test_user, "home_stop", "North High and Woodruff", _DUMMY_EMBEDDING)

        results = db.get_relevant_facts(test_user, _DUMMY_EMBEDDING, k=5)

        assert len(results) >= 1
        keys = [r["key"] for r in results]
        assert "home_stop" in keys


# ---------------------------------------------------------------------------
# Store 1 — Jobs
# ---------------------------------------------------------------------------

class TestJobsIntegration:
    def test_add_job_and_get_jobs(
        self, db: MemoryDB, test_user: str
    ):
        """An added job should appear in get_jobs() with the correct fields."""
        job = {
            "schedule": "0 8 * * 1-5",
            "prompt": "What is the next Route 10 bus?",
            "task_name": "check_bus_route_10",
            "category": "bus_transit",
            "description": "Daily morning bus check",
        }
        db.add_job(test_user, job)

        jobs = db.get_jobs(test_user)

        assert len(jobs) >= 1
        names = [j["task_name"] for j in jobs]
        assert "check_bus_route_10" in names

        saved = next(j for j in jobs if j["task_name"] == "check_bus_route_10")
        assert saved["schedule"] == "0 8 * * 1-5"

    def test_job_exists_true_and_false(
        self, db: MemoryDB, test_user: str
    ):
        """job_exists() should return True for an inserted job, False for an unknown name."""
        db.add_job(
            test_user,
            {
                "schedule": "0 9 * * *",
                "prompt": "Check grades",
                "task_name": "check_grades_daily",
                "category": "buckeyelink",
            },
        )

        assert db.job_exists(test_user, "check_grades_daily") is True
        assert db.job_exists(test_user, "this_job_does_not_exist") is False


# ---------------------------------------------------------------------------
# Migration 003 — last_reply column on profiles
# ---------------------------------------------------------------------------

class TestLastReplyColumn:
    """Verify migration 003: last_reply TEXT column on the profiles table."""

    def test_column_exists_and_is_nullable(self, supabase_client: Client, test_user: str):
        """A freshly created profile should have last_reply as NULL."""
        row = (
            supabase_client.table("profiles")
            .select("last_reply")
            .eq("id", test_user)
            .maybe_single()
            .execute()
        )
        assert row is not None and row.data is not None
        assert row.data.get("last_reply") is None

    def test_last_reply_round_trip(self, supabase_client: Client, test_user: str):
        """Writing last_reply and reading it back should return the exact value."""
        value = "South Green is open until 8pm."
        supabase_client.table("profiles").update({"last_reply": value}).eq("id", test_user).execute()

        row = (
            supabase_client.table("profiles")
            .select("last_reply")
            .eq("id", test_user)
            .maybe_single()
            .execute()
        )
        assert row is not None and row.data is not None
        assert row.data["last_reply"] == value
