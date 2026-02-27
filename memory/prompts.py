"""Granite LLM prompts and OpenAI embedding utilities for the memory module.

All Granite calls use the BeeAI ChatModel already configured in the project.
Embeddings use OpenAI text-embedding-3-small (1536 dims).
"""

import json
import logging
import os
from typing import Any

from beeai_framework.backend import ChatModel
from beeai_framework.backend.message import UserMessage
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Valid task categories. Granite must return one of these.
CATEGORIES = [
    "food_ordering",
    "bus_transit",
    "dining_hall",
    "canvas",
    "buckeyelink",
    "parking",
    "events",
    "library",
    "recsports",
    "athletics",
    "general",
]

_openai_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


async def embed(text: str) -> list[float]:
    """Embed text using OpenAI text-embedding-3-small (1536 dims)."""
    client = _get_openai()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def _parse_json_response(raw: str, context: str) -> dict[str, Any]:
    """Extract the first JSON object from a Granite response string."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON for %s. Raw: %r", context, raw)
        return {}


async def categorize_task(llm: ChatModel, task: str) -> str:
    """Ask Granite to assign one category tag to a task string.

    Returns one of the strings in CATEGORIES, defaulting to "general" on failure.
    """
    prompt = (
        f"Assign one category tag to this user task. "
        f"Choose exactly one from: {', '.join(CATEGORIES)}\n\n"
        f'Task: "{task}"\n\n'
        f'Reply with JSON only, no explanation: {{"category": "..."}}'
    )

    response = await llm.create(messages=[UserMessage(content=prompt)])
    raw = response.get_text_content()
    data = _parse_json_response(raw, "categorize_task")
    category = data.get("category", "general")
    return category if category in CATEGORIES else "general"


async def check_repetition(
    llm: ChatModel, task: str, same_category_tasks: list[str]
) -> dict[str, Any] | None:
    """Ask Granite whether a new task represents a repeating pattern.

    Args:
        llm: BeeAI ChatModel instance.
        task: The new task text.
        same_category_tasks: Recent tasks in the same category (last 30 days).

    Returns:
        A dict with keys {is_repeat, schedule, prompt, task_name, description}
        if a repetition is confirmed, or None if not a repeat.
        schedule may be None if there is no clear temporal pattern.
    """
    tasks_json = json.dumps(same_category_tasks, ensure_ascii=False)
    prompt = (
        "Does the new task represent a recurring activity that matches any tasks "
        "in the list below? A recurring activity means the user regularly does the "
        "same type of thing (not just similar words).\n\n"
        f'New task: "{task}"\n'
        f"Same-category recent tasks: {tasks_json}\n\n"
        "Reply with JSON only, no explanation:\n"
        "{\n"
        '  "is_repeat": true or false,\n'
        '  "schedule": "cron expression or null",\n'
        '  "prompt": "natural language prompt to send the agent when this runs",\n'
        '  "task_name": "snake_case_slug",\n'
        '  "description": "one sentence description"\n'
        "}\n"
        'Set "schedule" to null if repetition exists but no clear time pattern is detectable.'
    )

    response = await llm.create(messages=[UserMessage(content=prompt)])
    raw = response.get_text_content()
    data = _parse_json_response(raw, "check_repetition")

    if not data.get("is_repeat"):
        return None

    return {
        "is_repeat": True,
        "schedule": data.get("schedule"),
        "prompt": data.get("prompt", task),
        "task_name": data.get("task_name", "recurring_task"),
        "description": data.get("description"),
    }


async def extract_facts(llm: ChatModel, task: str) -> list[dict[str, str]]:
    """Ask Granite to extract personal facts from a user message.

    Returns a list of {key, value} dicts, or an empty list if nothing notable.
    Examples of facts: dietary preferences, home location, major, schedule patterns.
    """
    prompt = (
        "Extract any personal facts about the user from this message. "
        "Facts include: preferences (dietary, transit), locations (home stop, dorm), "
        "academic info (major, year), schedule patterns, or anything else that "
        "would help personalize future responses.\n\n"
        f'Message: "{task}"\n\n'
        'Reply with JSON only, no explanation: {"facts": [{"key": "...", "value": "..."}]}\n'
        'Return {"facts": []} if nothing notable is present.'
    )

    response = await llm.create(messages=[UserMessage(content=prompt)])
    raw = response.get_text_content()
    data = _parse_json_response(raw, "extract_facts")
    facts = data.get("facts", [])

    # Filter out malformed entries
    return [
        f for f in facts
        if isinstance(f, dict) and f.get("key") and f.get("value")
    ]
