"""Low-level Supabase CRUD for all 3 memory stores.

Store 1 — memory_jobs:   Recurring scheduled tasks detected by Granite.
Store 2 — memory_tasks:  30-day rolling window of categorized task history.
Store 3 — memory_facts:  Key-value user facts with pgvector embeddings.
"""

import logging
from datetime import datetime, timedelta, timezone

from supabase import Client

logger = logging.getLogger(__name__)

_TASK_RETENTION_DAYS = 30


class MemoryDB:
    def __init__(self, client: Client) -> None:
        self.client = client

    # ------------------------------------------------------------------
    # Store 2 — Recent task history
    # ------------------------------------------------------------------

    def push_task(self, user_id: str, task: str, category: str) -> None:
        """Insert a new task and prune entries older than 30 days for this user."""
        self.client.table("memory_tasks").insert(
            {"user_id": user_id, "task": task, "category": category}
        ).execute()

        cutoff = (
            datetime.now(tz=timezone.utc) - timedelta(days=_TASK_RETENTION_DAYS)
        ).isoformat()

        self.client.table("memory_tasks").delete().eq(
            "user_id", user_id
        ).lt("created_at", cutoff).execute()

    def get_tasks_by_category(self, user_id: str, category: str) -> list[str]:
        """Return task strings for the given user/category from the last 30 days.

        Returns plain task strings (not dicts) since that's what the LLM prompt needs.
        """
        cutoff = (
            datetime.now(tz=timezone.utc) - timedelta(days=_TASK_RETENTION_DAYS)
        ).isoformat()

        result = (
            self.client.table("memory_tasks")
            .select("task")
            .eq("user_id", user_id)
            .eq("category", category)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return [row["task"] for row in (result.data or [])]

    # ------------------------------------------------------------------
    # Store 3 — User facts
    # ------------------------------------------------------------------

    def upsert_fact(
        self, user_id: str, key: str, value: str, embedding: list[float]
    ) -> None:
        """Insert or update a user fact and its embedding.

        Uses Postgres UPSERT (ON CONFLICT user_id, key → UPDATE).
        """
        self.client.table("memory_facts").upsert(
            {
                "user_id": user_id,
                "key": key,
                "value": value,
                "embedding": embedding,
                "updated_at": datetime.now(tz=timezone.utc).isoformat(),
            },
            on_conflict="user_id,key",
        ).execute()

    def get_relevant_facts(
        self, user_id: str, query_embedding: list[float], k: int = 5
    ) -> list[dict]:
        """Return the top-k most semantically relevant facts via pgvector cosine search.

        Calls the `match_facts` Postgres function defined in the migration.

        Returns:
            List of dicts with keys: key, value, similarity (0–1 float).
        """
        result = self.client.rpc(
            "match_facts",
            {
                "query_embedding": query_embedding,
                "p_user_id": user_id,
                "match_count": k,
            },
        ).execute()
        return result.data or []

    def get_all_facts(self, user_id: str) -> list[dict]:
        """Return all facts for a user (key + value only, no embeddings).

        Used when no query embedding is available (e.g. new user with no history).
        """
        result = (
            self.client.table("memory_facts")
            .select("key, value")
            .eq("user_id", user_id)
            .execute()
        )
        return result.data or []

    # ------------------------------------------------------------------
    # Store 1 — Scheduled jobs
    # ------------------------------------------------------------------

    def get_jobs(self, user_id: str) -> list[dict]:
        """Return all scheduled jobs for a user."""
        result = (
            self.client.table("memory_jobs")
            .select("schedule, prompt, task_name, description, category, occurrence_count")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        return result.data or []

    def add_job(self, user_id: str, job: dict) -> None:
        """Insert a new scheduled job.

        Expected job keys: schedule, prompt, task_name, category,
        and optionally description.
        """
        self.client.table("memory_jobs").insert(
            {
                "user_id": user_id,
                "schedule": job["schedule"],
                "prompt": job["prompt"],
                "task_name": job["task_name"],
                "category": job["category"],
                "description": job.get("description"),
                "occurrence_count": job.get("occurrence_count", 1),
            }
        ).execute()

    def increment_job_occurrence(self, user_id: str, task_name: str) -> None:
        """Bump the occurrence counter on an existing job."""
        # Fetch current count first (Supabase-py doesn't support atomic increment directly)
        result = (
            self.client.table("memory_jobs")
            .select("id, occurrence_count")
            .eq("user_id", user_id)
            .eq("task_name", task_name)
            .maybe_single()
            .execute()
        )
        if result is None or not result.data:
            return
        new_count = result.data["occurrence_count"] + 1
        self.client.table("memory_jobs").update(
            {"occurrence_count": new_count}
        ).eq("id", result.data["id"]).execute()

    def job_exists(self, user_id: str, task_name: str) -> bool:
        """Check whether a job with this task_name already exists for the user."""
        result = (
            self.client.table("memory_jobs")
            .select("id")
            .eq("user_id", user_id)
            .eq("task_name", task_name)
            .maybe_single()
            .execute()
        )
        return result is not None and result.data is not None
