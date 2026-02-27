"""Shared pytest fixtures and auto-skip logic for the BuckeyeBot test suite.

Tests are organized into three credential tiers:
  - @pytest.mark.integration  requires SUPABASE_URL + SUPABASE_API_KEY
  - @pytest.mark.semantic     requires above + OPENAI_API_KEY
  - @pytest.mark.llm          requires WATSONX_API_KEY + WATSONX_PROJECT_ID (no Supabase needed)

Tests in each tier are automatically skipped when the required env vars are absent.
Set them in a .env file at the project root; this conftest loads it automatically.
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


# ---------------------------------------------------------------------------
# Marker registration + auto-skip
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: requires SUPABASE_URL and SUPABASE_API_KEY"
    )
    config.addinivalue_line(
        "markers", "semantic: requires Supabase + OPENAI_API_KEY for pgvector tests"
    )
    config.addinivalue_line(
        "markers", "llm: requires WATSONX_API_KEY + WATSONX_PROJECT_ID for Granite quality tests"
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    has_sb = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_API_KEY"))
    has_oai = bool(os.environ.get("OPENAI_API_KEY"))
    has_wx = bool(
        os.environ.get("WATSONX_API_KEY") and os.environ.get("WATSONX_PROJECT_ID")
    )

    for item in items:
        if "integration" in item.keywords and not has_sb:
            item.add_marker(
                pytest.mark.skip(reason="SUPABASE_URL / SUPABASE_API_KEY not set")
            )
        if "semantic" in item.keywords and not (has_sb and has_oai):
            item.add_marker(
                pytest.mark.skip(reason="SUPABASE + OPENAI_API_KEY not set")
            )
        if "llm" in item.keywords and not has_wx:
            item.add_marker(
                pytest.mark.skip(reason="WATSONX_API_KEY / WATSONX_PROJECT_ID not set")
            )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def supabase_client() -> Client:
    """Session-scoped real Supabase client. Requires SUPABASE_URL + SUPABASE_API_KEY."""
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_API_KEY"],
    )


@pytest.fixture
def test_user(supabase_client: Client) -> Iterator[str]:
    """Create a throwaway profile for one test; delete it (and all cascade rows) on teardown.

    Yields the profile UUID string.
    """
    phone = f"+1555{uuid.uuid4().hex[:7]}"
    result = supabase_client.table("profiles").insert({"phone": phone}).execute()
    user_id: str = result.data[0]["id"]
    yield user_id
    # ON DELETE CASCADE removes memory_tasks, memory_facts, memory_jobs automatically.
    supabase_client.table("profiles").delete().eq("id", user_id).execute()
