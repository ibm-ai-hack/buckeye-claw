"""Persistent token cache for BuckeyeMail OAuth tokens (SQLite)."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".buckeyemail_tokens.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS email_tokens (
    phone TEXT PRIMARY KEY,
    token_cache TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(_CREATE_TABLE)
    return conn


def save_token_cache(phone: str, serialized_cache: str) -> None:
    """Upsert a serialized MSAL token cache for a phone number."""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO email_tokens (phone, token_cache, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(phone) DO UPDATE SET token_cache=excluded.token_cache, updated_at=excluded.updated_at",
            (phone, serialized_cache, now),
        )


def load_token_cache(phone: str) -> str | None:
    """Retrieve the serialized MSAL token cache for a phone number."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT token_cache FROM email_tokens WHERE phone = ?", (phone,)
        ).fetchone()
    return row[0] if row else None


def delete_token_cache(phone: str) -> None:
    """Remove the token cache for a phone number."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM email_tokens WHERE phone = ?", (phone,))
