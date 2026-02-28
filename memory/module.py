"""MemoryModule — orchestrates the 3-body memory system.

Intended usage:
    # Fast read: call before agent runs (awaited, ~10–30ms DB read)
    context_str = await memory.get_context(user_id, current_task)

    # Fire-and-forget: call after agent replies (non-blocking)
    memory.update_background(user_id, task)

The get_context() method injects relevant user facts and scheduled jobs
into the agent's system prompt. The update_background() method runs
Granite categorization, repetition detection, and fact extraction in a
background thread so the agent's response latency is not affected.
"""

import asyncio
import logging
import threading

from beeai_framework.backend import ChatModel

from memory.db import MemoryDB
from memory.prompts import (
    CATEGORIES,
    categorize_task,
    check_repetition,
    embed,
    extract_facts,
)

logger = logging.getLogger(__name__)

# Only run repetition check when we have enough history to detect a pattern.
_MIN_TASKS_FOR_REPETITION_CHECK = 3


def _format_context(facts: list[dict], jobs: list[dict]) -> str:
    """Build a compact context string to prepend to the agent's system prompt."""
    parts: list[str] = []

    if facts:
        fact_strs = "; ".join(f"{f['key']}={f['value']}" for f in facts)
        parts.append(f"User facts: {fact_strs}.")

    if jobs:
        job_strs = "; ".join(
            f"{j['task_name']} ({j['schedule']})" if j.get("schedule")
            else j["task_name"]
            for j in jobs
        )
        parts.append(f"Recurring tasks: {job_strs}.")

    return " ".join(parts)


class MemoryModule:
    def __init__(self, llm: ChatModel, db: MemoryDB) -> None:
        self.llm = llm
        self.db = db

    async def get_context(self, user_id: str, current_task: str) -> str:
        """Return a context string to inject into the agent's system prompt.

        Performs a semantic search over user facts using the current task as
        the query. Also returns all scheduled jobs (typically small list).
        Falls back to returning all facts if embedding fails.

        This is awaited before the agent starts — kept fast by being pure DB reads.
        """
        jobs = self.db.get_jobs(user_id)

        try:
            query_embedding = await embed(current_task)
            facts = self.db.get_relevant_facts(user_id, query_embedding, k=5)
        except Exception:
            logger.warning("Embedding failed for get_context; falling back to all facts")
            facts = self.db.get_all_facts(user_id)

        return _format_context(facts, jobs)

    def update_background(self, user_id: str, task: str) -> None:
        """Trigger background update of all 3 memory stores.

        Spawns a daemon thread so the caller (webhook handler) is not blocked.
        Granite LLM calls happen inside this thread.
        """
        thread = threading.Thread(
            target=self._run_update,
            args=(user_id, task),
            daemon=True,
            name=f"memory-update-{user_id[:8]}",
        )
        thread.start()

    def _run_update(self, user_id: str, task: str) -> None:
        """Synchronous entry point for the background thread.

        Creates a fresh ChatModel to avoid aiohttp cross-loop errors — the main
        loop's ClientSession cannot be reused inside asyncio.run()'s new loop.
        """
        try:
            bg_llm = ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")
            asyncio.run(self._update(user_id, task, llm_override=bg_llm))
        except Exception:
            logger.exception("Memory update failed for user %s", user_id)

    async def _update(self, user_id: str, task: str, llm_override: ChatModel | None = None) -> None:
        """Full async update pipeline: categorize → store → check repeat → extract facts."""
        llm = llm_override or self.llm
        logger.info("[MEMORY-UPDATE] Starting update for user %s | task: %r", user_id, task)

        # Step 1: categorize the task (Granite call)
        try:
            category = await categorize_task(llm, task)
        except Exception:
            logger.warning("Categorization failed for task %r; using 'general'", task)
            category = "general"
        logger.info("[MEMORY-UPDATE] Categorized as: %s", category)

        # Step 2: push to task cache (auto-prunes >30 days)
        self.db.push_task(user_id, task, category)
        logger.info("[MEMORY-UPDATE] Pushed to memory_tasks (category=%s)", category)

        # Step 3: check for repetition within same category (Granite call)
        same_cat_tasks = self.db.get_tasks_by_category(user_id, category)
        logger.info("[MEMORY-UPDATE] Same-category task count: %d (need %d for repeat check)", len(same_cat_tasks), _MIN_TASKS_FOR_REPETITION_CHECK)
        if len(same_cat_tasks) >= _MIN_TASKS_FOR_REPETITION_CHECK:
            logger.info("[MEMORY-UPDATE] Running repetition check against: %s", same_cat_tasks)
            await self._handle_repetition(user_id, task, category, same_cat_tasks, llm)

        # Step 4: extract personal facts and embed + upsert each one (Granite + Voyage)
        await self._handle_fact_extraction(user_id, task, llm)

    async def _handle_repetition(
        self,
        user_id: str,
        task: str,
        category: str,
        same_cat_tasks: list[str],
        llm: ChatModel | None = None,
    ) -> None:
        try:
            result = await check_repetition(llm or self.llm, task, same_cat_tasks)
        except Exception:
            logger.warning("Repetition check failed for user %s", user_id)
            return

        if result is None:
            return

        task_name = result["task_name"]

        if self.db.job_exists(user_id, task_name):
            self.db.increment_job_occurrence(user_id, task_name)
            logger.debug("Incremented job occurrence: %s / %s", user_id, task_name)
        elif result.get("schedule"):
            # Only create a scheduled job if Granite detected a time pattern.
            self.db.add_job(
                user_id,
                {
                    "schedule": result["schedule"],
                    "prompt": result["prompt"],
                    "task_name": task_name,
                    "category": category,
                    "description": result.get("description"),
                },
            )
            logger.info("Created new scheduled job: %s / %s", user_id, task_name)
        else:
            logger.debug(
                "Repetition detected but no schedule pattern found: %s / %s",
                user_id,
                task_name,
            )

    async def _handle_fact_extraction(self, user_id: str, task: str, llm: ChatModel | None = None) -> None:
        try:
            facts = await extract_facts(llm or self.llm, task)
        except Exception:
            logger.warning("Fact extraction failed for user %s", user_id)
            return

        if facts:
            logger.info("[MEMORY-UPDATE] Extracted %d fact(s) from task:", len(facts))
            for f in facts:
                logger.info("  %s = %s", f.get("key", "?"), f.get("value", "?"))
        else:
            logger.info("[MEMORY-UPDATE] No facts extracted from task")

        for fact in facts:
            try:
                fact_text = f"{fact['key']}: {fact['value']}"
                embedding = await embed(fact_text)
                self.db.upsert_fact(user_id, fact["key"], fact["value"], embedding)
                logger.info("[MEMORY-UPDATE] Upserted fact: %s = %s", fact["key"], fact["value"])
            except Exception:
                logger.warning("Failed to upsert fact %r for user %s", fact, user_id)
