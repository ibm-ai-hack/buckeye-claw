import os
import logging

from messaging import chat_store
from messaging.client import LinqClient

logger = logging.getLogger(__name__)

_linq_client: LinqClient | None = None

# Valid iMessage tapback reaction types
REACTION_TYPES = {"love", "like", "dislike", "laugh", "emphasize", "question"}


def get_linq_client() -> LinqClient:
    global _linq_client
    if _linq_client is None:
        _linq_client = LinqClient(os.environ["LINQ_API_TOKEN"])
    return _linq_client


async def send_message(to: str, text: str) -> dict:
    """Send a text message via iMessage/RCS/SMS."""
    client = get_linq_client()
    from_number = os.environ["LINQ_FROM_NUMBER"]
    preferred = os.environ.get("LINQ_PREFERRED_SERVICE", "iMessage")

    chat_id = chat_store.get_chat_id(to)
    if not chat_id:
        resp = await client.create_chat(from_number, [to])
        chat_id = resp.get("chat", {}).get("id", "")
        if chat_id:
            chat_store.set_chat_id(to, chat_id)

    parts = [{"type": "text", "value": text}]
    return await client.send_message(chat_id, parts, service=preferred)


async def start_typing(to: str) -> None:
    """Show typing indicator (best-effort, fails silently)."""
    chat_id = chat_store.get_chat_id(to)
    if not chat_id:
        return
    try:
        await get_linq_client().start_typing(chat_id)
    except Exception:
        logger.debug("Failed to start typing indicator for %s", to)


async def stop_typing(to: str) -> None:
    """Stop typing indicator (best-effort, fails silently)."""
    chat_id = chat_store.get_chat_id(to)
    if not chat_id:
        return
    try:
        await get_linq_client().stop_typing(chat_id)
    except Exception:
        logger.debug("Failed to stop typing indicator for %s", to)


async def mark_read(to: str) -> None:
    """Send a read receipt (best-effort, fails silently)."""
    chat_id = chat_store.get_chat_id(to)
    if not chat_id:
        return
    try:
        await get_linq_client().mark_read(chat_id)
    except Exception:
        logger.debug("Failed to send read receipt for %s", to)


async def react_to_message(message_id: str, reaction: str = "like") -> None:
    """Add a tapback reaction to a message (best-effort, fails silently)."""
    if reaction not in REACTION_TYPES:
        logger.warning("Invalid reaction type %r, skipping", reaction)
        return
    try:
        await get_linq_client().add_reaction(message_id, reaction)
    except Exception:
        logger.debug("Failed to add reaction to %s", message_id)
