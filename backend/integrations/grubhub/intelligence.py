"""
LLM decision layer for Grubhub automation.

Called between Appium steps to make intelligent choices:
- Which restaurant in the search results matches the user's request?
- Which menu item is the right one?
- Is the current screen state what we expect?

Uses the watsonx REST API directly for synchronous one-shot calls.
"""

import json
import logging
import os
from difflib import SequenceMatcher

import httpx

logger = logging.getLogger(__name__)

_iam_token: str | None = None
_token_client: httpx.Client | None = None


def _get_iam_token() -> str:
    """Get or refresh an IAM bearer token from the watsonx API key."""
    global _iam_token
    if _iam_token:
        return _iam_token

    api_key = os.environ["WATSONX_API_KEY"]
    resp = httpx.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    _iam_token = resp.json()["access_token"]
    return _iam_token


def _generate(prompt: str, max_tokens: int = 150) -> str:
    """One-shot synchronous text generation via watsonx REST API."""
    token = _get_iam_token()
    api_url = os.environ.get("WATSONX_API_URL", "https://us-south.ml.cloud.ibm.com")
    project_id = os.environ["WATSONX_PROJECT_ID"]

    resp = httpx.post(
        f"{api_url}/ml/v1/text/generation?version=2024-05-31",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model_id": "ibm/granite-3-8b-instruct",
            "input": prompt,
            "project_id": project_id,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.1,
                "stop_sequences": ["\n\n"],
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if results:
        return results[0].get("generated_text", "").strip()
    return ""


# ── Decision functions ─────────────────────────────────────────────────


def pick_restaurant(query: str, results: list[dict]) -> int:
    """Pick the best restaurant from search results.

    Returns the index of the best match. Uses fuzzy matching first,
    falls back to LLM for ambiguous cases.
    """
    if not results:
        return 0

    names = [r["name"] for r in results]

    # Fast path: check for strong fuzzy match
    best_idx, best_score = 0, 0.0
    for i, name in enumerate(names):
        score = SequenceMatcher(None, query.lower(), name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_idx = i

    if best_score > 0.6:
        logger.info("Fuzzy match: '%s' → '%s' (score=%.2f)", query, names[best_idx], best_score)
        return best_idx

    # Ambiguous — ask the LLM
    try:
        numbered = "\n".join(f"{i}. {name}" for i, name in enumerate(names))
        prompt = (
            f"A user wants to order from \"{query}\". "
            f"Which of these restaurants is the best match?\n\n"
            f"{numbered}\n\n"
            f"Reply with ONLY the number of the best match."
        )
        answer = _generate(prompt, max_tokens=10)
        # Extract the first number from the response
        for char in answer:
            if char.isdigit():
                idx = int(char)
                if 0 <= idx < len(names):
                    logger.info("LLM match: '%s' → '%s' (idx=%d)", query, names[idx], idx)
                    return idx
    except Exception:
        logger.exception("LLM pick_restaurant failed, falling back to fuzzy match")

    return best_idx


def pick_menu_item(item_name: str, menu_items: list[dict]) -> str | None:
    """Find the best menu item matching what the user wants.

    Returns the exact name as it appears on the menu, or None if no match.
    """
    if not menu_items:
        return None

    names = [m["name"] for m in menu_items]

    # Fast path: exact substring match
    for name in names:
        if item_name.lower() in name.lower() or name.lower() in item_name.lower():
            logger.info("Substring match: '%s' → '%s'", item_name, name)
            return name

    # Fuzzy match
    best_name, best_score = names[0], 0.0
    for name in names:
        score = SequenceMatcher(None, item_name.lower(), name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_name = name

    if best_score > 0.5:
        logger.info("Fuzzy match: '%s' → '%s' (score=%.2f)", item_name, best_name, best_score)
        return best_name

    # Ambiguous — ask the LLM
    try:
        numbered = "\n".join(f"- {name}" for name in names)
        prompt = (
            f"A customer wants to order \"{item_name}\". "
            f"Which of these menu items is the best match?\n\n"
            f"{numbered}\n\n"
            f"Reply with ONLY the exact menu item name. "
            f"If nothing matches, reply \"NONE\"."
        )
        answer = _generate(prompt, max_tokens=50)
        answer_clean = answer.strip().strip('"').strip("'")

        if answer_clean.upper() == "NONE":
            logger.info("LLM says no match for '%s'", item_name)
            return None

        # Find the closest match to what the LLM returned
        for name in names:
            if answer_clean.lower() in name.lower() or name.lower() in answer_clean.lower():
                logger.info("LLM match: '%s' → '%s'", item_name, name)
                return name

        # LLM returned something we can't map — fall back to fuzzy best
        logger.warning("LLM returned '%s' which doesn't match any menu item", answer_clean)
    except Exception:
        logger.exception("LLM pick_menu_item failed, falling back to fuzzy match")

    return best_name if best_score > 0.3 else None


def parse_order_request(message: str) -> dict:
    """Extract item, restaurant, and time from a natural-language order request.

    Examples:
        "order a buckeye mocha from connecting grounds at 6pm"
        → {"item": "buckeye mocha", "restaurant": "connecting grounds", "time": "6pm"}

        "get me pizza from Blaze"
        → {"item": "pizza", "restaurant": "Blaze", "time": None}

    Returns dict with keys: item, restaurant, time (each str or None).
    """
    try:
        prompt = (
            "Extract the food order details from this message. "
            "Reply with ONLY a JSON object with keys: item, restaurant, time. "
            "Use null if not specified.\n\n"
            f'Message: "{message}"\n\n'
            "JSON:"
        )
        answer = _generate(prompt, max_tokens=100)
        # Find the JSON in the response
        start = answer.find("{")
        end = answer.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(answer[start:end])
            return {
                "item": parsed.get("item"),
                "restaurant": parsed.get("restaurant"),
                "time": parsed.get("time"),
            }
    except Exception:
        logger.exception("LLM parse_order_request failed")

    # Fallback: simple keyword extraction
    return _fallback_parse(message)


def _fallback_parse(message: str) -> dict:
    """Rule-based fallback parser when the LLM is unavailable."""
    msg = message.lower().strip()
    item, restaurant, time_str = None, None, None

    # Extract time: "at 6pm", "at 6:30 PM", "in 2 hours"
    import re
    time_match = re.search(
        r'(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm))|(?:in\s+\d+\s+(?:hour|min)\w*)',
        msg,
    )
    if time_match:
        time_str = time_match.group(0).strip()
        msg = msg[:time_match.start()] + msg[time_match.end():]

    # Extract restaurant: text after "from"
    from_match = re.search(r'\bfrom\s+(.+?)(?:\s+at\s|\s+in\s|$)', msg)
    if from_match:
        restaurant = from_match.group(1).strip().rstrip(",. ")
        msg = msg[:from_match.start()] + msg[from_match.end():]

    # Extract item: text after "order"/"get"/"buy"/"want" and before "from"
    item_match = re.search(
        r'(?:order|get|buy|grab|pick up|want)\s+(?:me\s+)?(?:a\s+|an\s+|some\s+)?(.+)',
        msg,
    )
    if item_match:
        item = item_match.group(1).strip().rstrip(",. ")
        # Clean up leftover modifiers
        item = re.sub(r'\s*default\s+everything\s*', '', item).strip()
        item = re.sub(r'\s*from\s+.*', '', item).strip()

    return {"item": item, "restaurant": restaurant, "time": time_str}


def describe_screen(visible_texts: list[str]) -> str:
    """Ask the LLM to summarize what screen we're on based on visible text.

    Useful for error recovery and debugging.
    """
    try:
        texts = ", ".join(f'"{t}"' for t in visible_texts[:20])
        prompt = (
            f"These text elements are visible on a Grubhub food ordering app screen: "
            f"[{texts}]. "
            f"In one short sentence, what screen or state is the app in?"
        )
        return _generate(prompt, max_tokens=50)
    except Exception:
        logger.exception("LLM describe_screen failed")
        return "unknown"
