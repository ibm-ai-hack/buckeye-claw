"""LLM quality / eval tests using the real IBM Granite model via watsonx.

These tests verify that Granite reliably categorizes tasks, extracts facts,
and detects repetition patterns from real user messages. They make live API
calls and are intentionally slow — run them separately during development.

Requirements:
    SUPABASE_URL, SUPABASE_API_KEY, WATSONX_API_KEY, WATSONX_PROJECT_ID must be set.

Run:
    pytest tests/test_llm_eval.py -v
"""

import pytest
from beeai_framework.backend import ChatModel

from memory.prompts import CATEGORIES, categorize_task, check_repetition, extract_facts

pytestmark = pytest.mark.llm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def llm() -> ChatModel:
    return ChatModel.from_name("watsonx:ibm/granite-3-8b-instruct")


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------

class TestCategorization:
    @pytest.mark.asyncio
    async def test_food_ordering(self, llm: ChatModel):
        result = await categorize_task(llm, "order a sandwich from Curl Market")
        assert result == "food_ordering", f"Expected 'food_ordering', got '{result}'"

    @pytest.mark.asyncio
    async def test_bus_transit(self, llm: ChatModel):
        result = await categorize_task(llm, "when does the next Route 10 bus come")
        assert result == "bus_transit", f"Expected 'bus_transit', got '{result}'"

    @pytest.mark.asyncio
    async def test_out_of_domain_returns_valid_category(self, llm: ChatModel):
        """Granite must not hallucinate a category outside the allowed list."""
        result = await categorize_task(llm, "what's the weather like today")
        assert result in CATEGORIES, (
            f"Got '{result}' which is not a valid category. "
            f"Granite hallucinated an out-of-domain value."
        )


# ---------------------------------------------------------------------------
# Fact extraction
# ---------------------------------------------------------------------------

class TestFactExtraction:
    @pytest.mark.asyncio
    async def test_extracts_dietary_preference(self, llm: ChatModel):
        facts = await extract_facts(llm, "I prefer vegetarian food")

        assert len(facts) > 0, "Expected at least one fact to be extracted"
        values = " ".join(f["value"].lower() for f in facts)
        assert "vegetarian" in values, (
            f"Expected 'vegetarian' in extracted values, got: {facts}"
        )

    @pytest.mark.asyncio
    async def test_no_facts_from_neutral_query(self, llm: ChatModel):
        facts = await extract_facts(llm, "what dining halls are open right now")

        assert facts == [], (
            f"Expected no facts from a neutral query, got: {facts}"
        )


# ---------------------------------------------------------------------------
# Repetition detection
# ---------------------------------------------------------------------------

class TestRepetitionDetection:
    @pytest.mark.asyncio
    async def test_detects_bus_pattern(self, llm: ChatModel):
        """Three similar bus queries should be recognized as a repeating pattern."""
        result = await check_repetition(
            llm,
            "next 10 bus",
            ["next 10 bus", "route 10 schedule", "when is the 10 coming"],
        )

        assert result is not None, "Expected repetition to be detected, got None"
        assert result["is_repeat"] is True
        assert result.get("task_name"), "Expected a non-empty task_name slug"
        assert result.get("prompt"), "Expected a non-empty agent prompt"
