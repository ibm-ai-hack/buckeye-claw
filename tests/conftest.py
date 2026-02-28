"""Shared pytest fixtures and auto-skip logic for the BuckeyeBot test suite.

Tests are organized into four credential tiers:
  - @pytest.mark.integration  requires SUPABASE_URL + SUPABASE_API_KEY
  - @pytest.mark.semantic     requires above + VOYAGE_API_KEY
  - @pytest.mark.llm          requires WATSONX_API_KEY + WATSONX_PROJECT_ID (no Supabase needed)
  - @pytest.mark.e2e          requires all of the above (full MemoryModule pipeline)

Tests in each tier are automatically skipped when the required env vars are absent.
Set them in a .env file at the project root; this conftest loads it automatically.

Migration auto-apply:
  Set SUPABASE_DB_PASSWORD in .env and the session fixture will automatically apply
  supabase/migrations/002_voyage_embedding.sql (VECTOR 1536→1024) if not yet applied.
  Without this, tests that write embeddings will fail with a clear schema error.
"""

import logging
import os
import uuid
import warnings
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

logger = logging.getLogger(__name__)

_MIGRATION_002 = Path(__file__).parent.parent / "supabase" / "migrations" / "002_voyage_embedding.sql"


# ---------------------------------------------------------------------------
# Marker registration + auto-skip
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: requires SUPABASE_URL and SUPABASE_API_KEY"
    )
    config.addinivalue_line(
        "markers", "semantic: requires Supabase + VOYAGE_API_KEY for pgvector tests"
    )
    config.addinivalue_line(
        "markers", "llm: requires WATSONX_API_KEY + WATSONX_PROJECT_ID for Granite quality tests"
    )
    config.addinivalue_line(
        "markers",
        "e2e: requires Supabase + Voyage AI + WATSONX credentials for full MemoryModule pipeline tests",
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    has_sb = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_API_KEY"))
    has_voyage = bool(os.environ.get("VOYAGE_API_KEY"))
    has_wx = bool(
        os.environ.get("WATSONX_API_KEY") and os.environ.get("WATSONX_PROJECT_ID")
    )

    for item in items:
        if "integration" in item.keywords and not has_sb:
            item.add_marker(
                pytest.mark.skip(reason="SUPABASE_URL / SUPABASE_API_KEY not set")
            )
        if "semantic" in item.keywords and not (has_sb and has_voyage):
            item.add_marker(
                pytest.mark.skip(reason="SUPABASE + VOYAGE_API_KEY not set")
            )
        if "llm" in item.keywords and not has_wx:
            item.add_marker(
                pytest.mark.skip(reason="WATSONX_API_KEY / WATSONX_PROJECT_ID not set")
            )
        if "e2e" in item.keywords and not (has_sb and has_voyage and has_wx):
            item.add_marker(
                pytest.mark.skip(reason="e2e requires SUPABASE + VOYAGE_API_KEY + WATSONX credentials")
            )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _probe_embedding_dim(client: Client) -> int | None:
    """Return the enforced dimension of memory_facts.embedding by using a temp profile.

    Creates a throwaway profile, tries to upsert a 1024-dim embedding, reads the
    outcome, then deletes the profile (cascade removes the fact row too).

    Returns 1024 if the column accepts 1024-dim vectors, 1536 if it rejects them
    with a dimension error, or None if detection fails for any other reason.
    """
    phone = f"+155500000{uuid.uuid4().hex[:4]}"
    try:
        profile_resp = client.table("profiles").insert({"phone": phone}).execute()
        probe_user_id: str = profile_resp.data[0]["id"]
    except Exception:
        return None

    detected_dim: int | None = None
    try:
        client.table("memory_facts").upsert(
            {
                "user_id": probe_user_id,
                "key": "_schema_probe",
                "value": "_probe",
                "embedding": [0.0] * 1024,
                "updated_at": "2000-01-01T00:00:00+00:00",
            },
            on_conflict="user_id,key",
        ).execute()
        detected_dim = 1024  # upsert succeeded → column accepts 1024 dims
    except Exception as exc:
        msg = str(exc)
        if "expected" in msg and "dimensions" in msg:
            detected_dim = 1536  # explicit dimension mismatch → column is VECTOR(1536)
        # else: some other error — detected_dim stays None
    finally:
        try:
            client.table("profiles").delete().eq("id", probe_user_id).execute()
        except Exception:
            pass

    return detected_dim


def _apply_migration_002(project_ref: str, password: str) -> None:
    """Apply 002_voyage_embedding.sql via direct PostgreSQL connection (pg8000)."""
    import pg8000.native  # noqa: PLC0415

    sql = _MIGRATION_002.read_text()
    conn = pg8000.native.Connection(
        host="aws-0-us-east-1.pooler.supabase.com",
        port=5432,
        user=f"postgres.{project_ref}",
        password=password,
        database="postgres",
        timeout=30,
    )
    try:
        # pg8000 doesn't support multi-statement strings; split by semicolons.
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                conn.run(stmt)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def ensure_migration_002() -> None:
    """Session fixture: verify that migration 002 (VECTOR 1536→1024) is applied.

    Only runs when SUPABASE_URL + SUPABASE_API_KEY are set (i.e. for integration
    tests). Skips silently for unit-only runs.

    If SUPABASE_DB_PASSWORD is set, automatically applies the migration via a
    direct pg8000 connection to the Supabase session-mode pooler.

    If the migration is not applied and cannot be auto-applied, all e2e tests are
    skipped with a clear error pointing to the migration file.
    """
    if not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_API_KEY")):
        return  # No Supabase credentials → nothing to check

    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_API_KEY"])
    actual_dim = _probe_embedding_dim(client)

    if actual_dim == 1024:
        return  # Migration already applied

    if actual_dim is None:
        logger.warning("Could not detect embedding column dimension; proceeding anyway.")
        return

    # actual_dim == 1536 → migration 002 not applied.
    db_password = os.environ.get("SUPABASE_DB_PASSWORD")
    if db_password:
        url = os.environ["SUPABASE_URL"]
        project_ref = url.split("//")[1].split(".")[0]
        try:
            _apply_migration_002(project_ref, db_password)
            logger.info("Migration 002 applied automatically via SUPABASE_DB_PASSWORD")
            return
        except Exception as exc:
            logger.warning(
                "Failed to auto-apply migration 002 via SUPABASE_DB_PASSWORD: %s. "
                "Apply supabase/migrations/002_voyage_embedding.sql manually.",
                exc,
            )

    warnings.warn(
        "\n\n"
        "  SCHEMA MISMATCH: memory_facts.embedding is VECTOR(1536) but\n"
        "  the code produces 1024-dim Voyage AI embeddings.\n"
        "  Embedding-related tests will fail until migration 002 is applied.\n\n"
        "  Fix: Run supabase/migrations/002_voyage_embedding.sql in the Supabase\n"
        "  SQL Editor, or set SUPABASE_DB_PASSWORD in .env to auto-apply it.\n",
        UserWarning,
        stacklevel=2,
    )


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
