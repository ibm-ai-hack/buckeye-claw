"""Persistent token cache for BuckeyeMail OAuth tokens (SQLite)."""

import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".buckeyemail_tokens.db"

_CREATE_TOKENS = """
CREATE TABLE IF NOT EXISTS email_tokens (
    phone TEXT PRIMARY KEY,
    token_cache TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_CREATE_AUTH_LINKS = """
CREATE TABLE IF NOT EXISTS auth_links (
    code       TEXT PRIMARY KEY,
    phone      TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

_LINK_EXPIRY_MINUTES = 15


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(_CREATE_TOKENS)
    conn.execute(_CREATE_AUTH_LINKS)
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


# ---------------------------------------------------------------------------
# Short-lived auth links (single-use codes for SMS onboarding)
# ---------------------------------------------------------------------------


def create_auth_link(phone: str) -> str:
    """Create a short random code that maps to a phone number. Returns the code."""
    code = secrets.token_urlsafe(8)
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO auth_links (code, phone, created_at) VALUES (?, ?, ?)",
            (code, phone, now),
        )
    return code


def consume_auth_link(code: str) -> str | None:
    """Look up and delete an auth link, returning the phone number or None.

    Returns None if the code doesn't exist or has expired (>15 min).
    """
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT phone, created_at FROM auth_links WHERE code = ?", (code,)
        ).fetchone()
        if not row:
            return None
        phone, created_at = row
        # Check expiry
        created = datetime.fromisoformat(created_at)
        age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
        # Always delete the code (single-use)
        conn.execute("DELETE FROM auth_links WHERE code = ?", (code,))
        if age_minutes > _LINK_EXPIRY_MINUTES:
            return None
        return phone
