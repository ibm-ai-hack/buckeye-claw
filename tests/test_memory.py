"""Tests for the memory/ module.

Unit tests mock both the Supabase client and the LLM.
Integration tests (marked @pytest.mark.integration) require live credentials.

Run unit tests only:
    pytest tests/test_memory.py -m "not integration"

Run all including integration:
    pytest tests/test_memory.py --run-integration
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from memory.db import MemoryDB
from memory.module import MemoryModule, _format_context


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    """A MagicMock Supabase client with chainable query methods pre-wired."""
    client = MagicMock()

    def make_chain(return_data):
        chain = MagicMock()
        chain.execute.return_value = MagicMock(data=return_data)
        # make every chained call return itself so arbitrary chains work
        chain.eq = MagicMock(return_value=chain)
        chain.lt = MagicMock(return_value=chain)
        chain.gte = MagicMock(return_value=chain)
        chain.order = MagicMock(return_value=chain)
        chain.maybe_single = MagicMock(return_value=chain)
        return chain

    client._make_chain = make_chain
    return client


@pytest.fixture
def db(mock_client):
    return MemoryDB(mock_client)


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    # Default: categorize returns "general"
    response = MagicMock()
    response.get_text_content.return_value = '{"category": "general"}'
    llm.create = AsyncMock(return_value=response)
    return llm


@pytest.fixture
def memory_module(mock_llm, db):
    return MemoryModule(llm=mock_llm, db=db)


USER_ID = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# MemoryDB — Store 2 (Tasks)
# ---------------------------------------------------------------------------

class TestPushTask:
    def test_inserts_task_with_category(self, mock_client, db):
        insert_chain = MagicMock()
        insert_chain.execute.return_value = MagicMock(data=[{"id": str(uuid.uuid4())}])
        mock_client.table.return_value.insert.return_value = insert_chain

        delete_chain = MagicMock()
        delete_chain.execute.return_value = MagicMock(data=[])
        delete_chain.eq = MagicMock(return_value=delete_chain)
        delete_chain.lt = MagicMock(return_value=delete_chain)
        mock_client.table.return_value.delete.return_value = delete_chain

        db.push_task(USER_ID, "next 10 bus", "bus_transit")

        mock_client.table.return_value.insert.assert_called_once_with(
            {"user_id": USER_ID, "task": "next 10 bus", "category": "bus_transit"}
        )

    def test_prunes_old_tasks_on_push(self, mock_client, db):
        """After inserting, a DELETE is issued to prune tasks older than 30 days."""
        insert_chain = MagicMock()
        insert_chain.execute.return_value = MagicMock(data=[{}])
        mock_client.table.return_value.insert.return_value = insert_chain

        delete_chain = MagicMock()
        delete_chain.execute.return_value = MagicMock(data=[])
        delete_chain.eq = MagicMock(return_value=delete_chain)
        delete_chain.lt = MagicMock(return_value=delete_chain)
        mock_client.table.return_value.delete.return_value = delete_chain

        db.push_task(USER_ID, "check bus", "bus_transit")

        mock_client.table.return_value.delete.assert_called_once()
        delete_chain.eq.assert_called_with("user_id", USER_ID)
        delete_chain.lt.assert_called_once()  # cutoff timestamp passed


class TestGetTasksByCategory:
    def test_returns_tasks_in_category(self, mock_client, db):
        rows = [{"task": "order pizza"}, {"task": "order sushi"}]
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=rows)
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.gte = MagicMock(return_value=select_chain)
        select_chain.order = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        result = db.get_tasks_by_category(USER_ID, "food_ordering")

        assert result == ["order pizza", "order sushi"]

    def test_returns_empty_list_when_none(self, mock_client, db):
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=None)
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.gte = MagicMock(return_value=select_chain)
        select_chain.order = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        result = db.get_tasks_by_category(USER_ID, "bus_transit")

        assert result == []


# ---------------------------------------------------------------------------
# MemoryDB — Store 3 (Facts)
# ---------------------------------------------------------------------------

class TestUpsertFact:
    def test_upsert_called_with_correct_args(self, mock_client, db):
        upsert_chain = MagicMock()
        upsert_chain.execute.return_value = MagicMock(data=[{}])
        mock_client.table.return_value.upsert.return_value = upsert_chain

        embedding = [0.1] * 1024
        db.upsert_fact(USER_ID, "dietary_pref", "vegetarian", embedding)

        call_args = mock_client.table.return_value.upsert.call_args
        payload = call_args[0][0]
        assert payload["user_id"] == USER_ID
        assert payload["key"] == "dietary_pref"
        assert payload["value"] == "vegetarian"
        assert payload["embedding"] == embedding

    def test_on_conflict_is_set(self, mock_client, db):
        upsert_chain = MagicMock()
        upsert_chain.execute.return_value = MagicMock(data=[{}])
        mock_client.table.return_value.upsert.return_value = upsert_chain

        db.upsert_fact(USER_ID, "key", "value", [0.0] * 1024)

        call_kwargs = mock_client.table.return_value.upsert.call_args[1]
        assert call_kwargs.get("on_conflict") == "user_id,key"


class TestGetRelevantFacts:
    def test_calls_rpc_match_facts(self, mock_client, db):
        facts = [
            {"key": "home_stop", "value": "North High", "similarity": 0.92},
            {"key": "dietary_pref", "value": "vegetarian", "similarity": 0.65},
        ]
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=facts)

        embedding = [0.1] * 1024
        result = db.get_relevant_facts(USER_ID, embedding, k=5)

        mock_client.rpc.assert_called_once_with(
            "match_facts",
            {"query_embedding": embedding, "p_user_id": USER_ID, "match_count": 5},
        )
        assert result == facts

    def test_returns_empty_list_on_no_data(self, mock_client, db):
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=None)

        result = db.get_relevant_facts(USER_ID, [0.0] * 1024)

        assert result == []


# ---------------------------------------------------------------------------
# MemoryDB — Store 1 (Jobs)
# ---------------------------------------------------------------------------

class TestJobOperations:
    def test_add_job_inserts_row(self, mock_client, db):
        insert_chain = MagicMock()
        insert_chain.execute.return_value = MagicMock(data=[{}])
        mock_client.table.return_value.insert.return_value = insert_chain

        job = {
            "schedule": "0 8 * * 1-5",
            "prompt": "Check next Route 10 bus",
            "task_name": "check_bus_route_10",
            "category": "bus_transit",
            "description": "Daily morning bus check",
        }
        db.add_job(USER_ID, job)

        call_payload = mock_client.table.return_value.insert.call_args[0][0]
        assert call_payload["schedule"] == "0 8 * * 1-5"
        assert call_payload["task_name"] == "check_bus_route_10"

    def test_get_jobs_returns_list(self, mock_client, db):
        rows = [{"schedule": "0 8 * * 1-5", "task_name": "check_bus"}]
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=rows)
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.order = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        result = db.get_jobs(USER_ID)

        assert result == rows

    def test_job_exists_true(self, mock_client, db):
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data={"id": str(uuid.uuid4())})
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.maybe_single = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        assert db.job_exists(USER_ID, "check_bus_route_10") is True

    def test_job_exists_false(self, mock_client, db):
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=None)
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.maybe_single = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        assert db.job_exists(USER_ID, "nonexistent") is False


# ---------------------------------------------------------------------------
# _format_context helper
# ---------------------------------------------------------------------------

class TestFormatContext:
    def test_empty_facts_and_jobs(self):
        assert _format_context([], []) == ""

    def test_facts_only(self):
        facts = [{"key": "dietary_pref", "value": "vegetarian"}]
        result = _format_context(facts, [])
        assert "dietary_pref=vegetarian" in result

    def test_jobs_only(self):
        jobs = [{"task_name": "check_bus", "schedule": "0 8 * * 1-5"}]
        result = _format_context([], jobs)
        assert "check_bus" in result
        assert "0 8 * * 1-5" in result

    def test_job_without_schedule(self):
        jobs = [{"task_name": "order_food", "schedule": None}]
        result = _format_context([], jobs)
        assert "order_food" in result

    def test_facts_and_jobs_combined(self):
        facts = [{"key": "major", "value": "CSE"}]
        jobs = [{"task_name": "check_grades", "schedule": "0 9 * * 1"}]
        result = _format_context(facts, jobs)
        assert "major=CSE" in result
        assert "check_grades" in result


# ---------------------------------------------------------------------------
# MemoryModule — get_context
# ---------------------------------------------------------------------------

class TestGetContext:
    @pytest.mark.asyncio
    async def test_returns_empty_string_for_new_user(self, memory_module, mock_client):
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=[])

        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=[])
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.order = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        with patch("memory.module.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1024
            result = await memory_module.get_context(USER_ID, "check bus")

        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_context_with_facts_and_jobs(self, memory_module, mock_client):
        # get_relevant_facts
        facts = [{"key": "dietary_pref", "value": "vegetarian", "similarity": 0.9}]
        mock_client.rpc.return_value.execute.return_value = MagicMock(data=facts)

        # get_jobs
        jobs = [{"task_name": "check_bus", "schedule": "0 8 * * 1-5",
                 "description": None, "category": "bus_transit", "occurrence_count": 3,
                 "prompt": "Check next bus"}]
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=jobs)
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.order = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        with patch("memory.module.embed", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1024
            result = await memory_module.get_context(USER_ID, "next bus")

        assert "dietary_pref=vegetarian" in result
        assert "check_bus" in result

    @pytest.mark.asyncio
    async def test_falls_back_to_all_facts_on_embed_failure(self, memory_module, mock_client):
        all_facts = [{"key": "major", "value": "CSE"}]

        # get_jobs
        jobs_chain = MagicMock()
        jobs_chain.execute.return_value = MagicMock(data=[])
        jobs_chain.eq = MagicMock(return_value=jobs_chain)
        jobs_chain.order = MagicMock(return_value=jobs_chain)
        mock_client.table.return_value.select.return_value = jobs_chain

        # get_all_facts (fallback)
        all_facts_chain = MagicMock()
        all_facts_chain.execute.return_value = MagicMock(data=all_facts)
        all_facts_chain.eq = MagicMock(return_value=all_facts_chain)

        with patch("memory.module.embed", side_effect=Exception("OpenAI down")):
            with patch.object(memory_module.db, "get_all_facts", return_value=all_facts):
                result = await memory_module.get_context(USER_ID, "check grades")

        assert "major=CSE" in result


# ---------------------------------------------------------------------------
# MemoryModule — _update (Granite call integration)
# ---------------------------------------------------------------------------

class TestMemoryUpdate:
    @pytest.mark.asyncio
    async def test_categorizes_food_ordering_task(self, memory_module, mock_llm, mock_client):
        mock_llm.create = AsyncMock(
            return_value=MagicMock(
                get_text_content=MagicMock(return_value='{"category": "food_ordering"}')
            )
        )

        # Wire push_task
        insert_chain = MagicMock()
        insert_chain.execute.return_value = MagicMock(data=[{}])
        mock_client.table.return_value.insert.return_value = insert_chain

        delete_chain = MagicMock()
        delete_chain.execute.return_value = MagicMock(data=[])
        delete_chain.eq = MagicMock(return_value=delete_chain)
        delete_chain.lt = MagicMock(return_value=delete_chain)
        mock_client.table.return_value.delete.return_value = delete_chain

        # get_tasks_by_category returns < 3 → skip repetition check
        select_chain = MagicMock()
        select_chain.execute.return_value = MagicMock(data=[{"task": "order pizza"}])
        select_chain.eq = MagicMock(return_value=select_chain)
        select_chain.gte = MagicMock(return_value=select_chain)
        select_chain.order = MagicMock(return_value=select_chain)
        mock_client.table.return_value.select.return_value = select_chain

        with patch("memory.module.embed", new_callable=AsyncMock, return_value=[0.0] * 1024):
            with patch("memory.module.extract_facts", new_callable=AsyncMock, return_value=[]):
                await memory_module._update(USER_ID, "order sandwich from Curl Market")

        insert_call = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_call["category"] == "food_ordering"

    @pytest.mark.asyncio
    async def test_repetition_creates_job(self, memory_module, mock_client):
        """When 5 same-category tasks exist and Granite confirms repetition, a job is created."""
        five_tasks = [
            "next 10 bus", "route 10 bus", "when is the 10",
            "next bus to class", "route 10 schedule",
        ]

        with (
            patch("memory.module.categorize_task", new_callable=AsyncMock, return_value="bus_transit"),
            patch.object(memory_module.db, "push_task"),
            patch.object(memory_module.db, "get_tasks_by_category", return_value=five_tasks),
            patch.object(memory_module.db, "job_exists", return_value=False),
            patch.object(memory_module.db, "add_job") as mock_add_job,
            patch("memory.module.check_repetition", new_callable=AsyncMock, return_value={
                "is_repeat": True,
                "schedule": "0 8 * * 1-5",
                "prompt": "What is the next Route 10 bus?",
                "task_name": "check_bus_route_10",
                "description": "Daily morning bus check",
            }),
            patch("memory.module.extract_facts", new_callable=AsyncMock, return_value=[]),
            patch("memory.module.embed", new_callable=AsyncMock, return_value=[0.0] * 1024),
        ):
            await memory_module._update(USER_ID, "next 10 bus")

        mock_add_job.assert_called_once()
        job_arg = mock_add_job.call_args[0][1]
        assert job_arg["task_name"] == "check_bus_route_10"
        assert job_arg["schedule"] == "0 8 * * 1-5"

    @pytest.mark.asyncio
    async def test_no_false_repetition_with_varied_tasks(self, memory_module):
        """Five varied tasks in the same category should not create a job."""
        varied_tasks = [
            "order pizza", "check my canvas", "bus schedule",
            "library hours", "dining menu",
        ]

        with (
            patch("memory.module.categorize_task", new_callable=AsyncMock, return_value="general"),
            patch.object(memory_module.db, "push_task"),
            patch.object(memory_module.db, "get_tasks_by_category", return_value=varied_tasks),
            patch.object(memory_module.db, "job_exists", return_value=False),
            patch.object(memory_module.db, "add_job") as mock_add_job,
            patch("memory.module.check_repetition", new_callable=AsyncMock, return_value=None),
            patch("memory.module.extract_facts", new_callable=AsyncMock, return_value=[]),
            patch("memory.module.embed", new_callable=AsyncMock, return_value=[0.0] * 1024),
        ):
            await memory_module._update(USER_ID, "random task")

        mock_add_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_fact_extraction_upserts_fact(self, memory_module):
        """A message containing a personal fact should upsert it to the facts store."""
        extracted = [{"key": "dietary_pref", "value": "vegetarian"}]

        with (
            patch("memory.module.categorize_task", new_callable=AsyncMock, return_value="general"),
            patch.object(memory_module.db, "push_task"),
            patch.object(memory_module.db, "get_tasks_by_category", return_value=[]),
            patch("memory.module.extract_facts", new_callable=AsyncMock, return_value=extracted),
            patch("memory.module.embed", new_callable=AsyncMock, return_value=[0.5] * 1024),
            patch.object(memory_module.db, "upsert_fact") as mock_upsert,
        ):
            await memory_module._update(USER_ID, "I prefer vegetarian food")

        mock_upsert.assert_called_once_with(
            USER_ID, "dietary_pref", "vegetarian", [0.5] * 1024
        )

    @pytest.mark.asyncio
    async def test_fact_embedding_stored(self, memory_module):
        """Upserted facts include a non-trivial embedding vector."""
        embedding = [float(i) / 1024 for i in range(1024)]
        extracted = [{"key": "major", "value": "CSE"}]

        with (
            patch("memory.module.categorize_task", new_callable=AsyncMock, return_value="general"),
            patch.object(memory_module.db, "push_task"),
            patch.object(memory_module.db, "get_tasks_by_category", return_value=[]),
            patch("memory.module.extract_facts", new_callable=AsyncMock, return_value=extracted),
            patch("memory.module.embed", new_callable=AsyncMock, return_value=embedding),
            patch.object(memory_module.db, "upsert_fact") as mock_upsert,
        ):
            await memory_module._update(USER_ID, "I'm studying CSE")

        call_embedding = mock_upsert.call_args[0][3]
        assert len(call_embedding) == 1024
        assert any(v != 0.0 for v in call_embedding)
