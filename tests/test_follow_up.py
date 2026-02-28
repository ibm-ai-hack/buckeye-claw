"""Tests for follow-up detection: _persist_last_reply, PipelineState.last_reply,
and _build_intake_prompt.

Unit tests only — no credentials or network calls required.

Run:
    pytest tests/test_follow_up.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

from agents.models import PipelineState
from agents.orchestrator import _build_intake_prompt


# ---------------------------------------------------------------------------
# _persist_last_reply (webhook.py)
# ---------------------------------------------------------------------------

class TestPersistLastReply:
    """Unit tests for backend.messaging.webhook._persist_last_reply."""

    @pytest.mark.asyncio
    async def test_writes_correct_supabase_call(self):
        """Should UPDATE profiles.last_reply for the correct phone number."""
        from backend.messaging.webhook import _persist_last_reply

        mock_client = MagicMock()
        with patch("auth.get_client", return_value=mock_client):
            await _persist_last_reply("+16141234567", "Bus 2 runs until midnight.")

        mock_client.table.assert_called_once_with("profiles")
        mock_client.table.return_value.update.assert_called_once_with(
            {"last_reply": "Bus 2 runs until midnight."}
        )
        mock_client.table.return_value.update.return_value.eq.assert_called_once_with(
            "phone", "+16141234567"
        )
        mock_client.table.return_value.update.return_value.eq.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_swallows_supabase_exception(self):
        """Should not raise even when Supabase throws — just logs a warning."""
        from backend.messaging.webhook import _persist_last_reply

        with patch("auth.get_client", side_effect=RuntimeError("connection refused")):
            await _persist_last_reply("+16141234567", "some reply")


# ---------------------------------------------------------------------------
# PipelineState.last_reply (models.py)
# ---------------------------------------------------------------------------

class TestPipelineStateLastReply:
    """Unit tests for the last_reply field on PipelineState."""

    def test_default_is_empty_string(self):
        state = PipelineState(user_text="hi", from_number="+16141234567")
        assert state.last_reply == ""

    def test_value_is_preserved(self):
        state = PipelineState(
            user_text="hi",
            from_number="+16141234567",
            last_reply="Bus runs until 11pm.",
        )
        assert state.last_reply == "Bus runs until 11pm."


# ---------------------------------------------------------------------------
# _build_intake_prompt (orchestrator.py)
# ---------------------------------------------------------------------------

class TestIntakePromptBuilding:
    """Unit tests for agents.orchestrator._build_intake_prompt.

    No LLM or workflow required — tests the pure string-building logic.
    """

    def test_prior_block_absent_when_last_reply_empty(self):
        prompt = _build_intake_prompt("", "", "what buses run near campus?")
        assert "Last message you sent to this user:" not in prompt

    def test_prior_block_present_when_last_reply_set(self):
        prompt = _build_intake_prompt("", "Bus 2 runs until midnight.", "and what about Route 10?")
        assert "Last message you sent to this user: Bus 2 runs until midnight." in prompt

    def test_user_text_always_present(self):
        prompt = _build_intake_prompt("", "", "what's for lunch?")
        assert "what's for lunch?" in prompt

    def test_memory_block_and_prior_block_both_present_in_order(self):
        """Memory context should appear before the prior_block."""
        prompt = _build_intake_prompt(
            "user is vegetarian",
            "South Green closes at 8pm.",
            "what about north campus?",
        )
        mem_pos = prompt.index("Known user context:")
        prior_pos = prompt.index("Last message you sent to this user:")
        assert mem_pos < prior_pos

    def test_empty_inputs_produce_minimal_prompt(self):
        """With no context or prior reply, only the classification instructions appear."""
        prompt = _build_intake_prompt("", "", "what's for lunch?")
        assert "Known user context:" not in prompt
        assert "Last message you sent to this user:" not in prompt
        assert "Classify the following user message" in prompt
