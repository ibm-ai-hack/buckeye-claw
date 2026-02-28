"""Tests for the auth/ module.

Unit tests mock the Supabase client. Integration tests (marked with
@pytest.mark.integration) require SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
in the environment and a live Supabase project.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from auth.users import get_user, get_user_by_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(select_data=None, insert_data=None):
    """Build a minimal mock Supabase client for auth operations."""
    client = MagicMock()

    # Chain: .table().select().eq().maybe_single().execute()
    select_chain = MagicMock()
    select_chain.execute.return_value = MagicMock(data=select_data)
    (
        client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
    ) = select_chain

    # Chain: .table().insert().execute()
    insert_chain = MagicMock()
    insert_chain.execute.return_value = MagicMock(data=insert_data or [])
    client.table.return_value.insert.return_value = insert_chain

    return client


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

class TestGetUser:
    def test_returns_existing_user_id(self):
        """When a profile exists for the phone, returns its ID."""
        existing_id = str(uuid.uuid4())
        client = _make_client(select_data={"id": existing_id})

        result = get_user(client, "+16141234567")

        assert result == existing_id
        client.table.return_value.insert.assert_not_called()

    def test_returns_none_when_not_found(self):
        """When no profile exists, returns None without inserting."""
        client = _make_client(select_data=None)

        result = get_user(client, "+16141234567")

        assert result is None
        client.table.return_value.insert.assert_not_called()

    def test_same_phone_same_id(self):
        """Two calls with the same phone return the same ID."""
        existing_id = str(uuid.uuid4())
        client = _make_client(select_data={"id": existing_id})

        id1 = get_user(client, "+16141234567")
        id2 = get_user(client, "+16141234567")

        assert id1 == id2 == existing_id


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

class TestGetUserById:
    def test_returns_profile_when_found(self):
        """Returns the full profile dict when the ID exists."""
        profile = {
            "id": str(uuid.uuid4()),
            "phone": "+16141234567",
            "email": None,
            "auth_id": None,
        }
        client = _make_client(select_data=profile)

        result = get_user_by_id(client, profile["id"])

        assert result == profile

    def test_returns_none_when_not_found(self):
        """Returns None when no profile matches the ID."""
        client = _make_client(select_data=None)

        result = get_user_by_id(client, str(uuid.uuid4()))

        assert result is None
