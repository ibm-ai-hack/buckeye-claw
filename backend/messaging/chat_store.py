import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_store: dict[str, str] = {}  # phone_number -> chat_id
_store_path: Path = Path(__file__).resolve().parent.parent / ".linq_chats.json"


def get_chat_id(phone_number: str) -> str | None:
    return _store.get(phone_number)


def set_chat_id(phone_number: str, chat_id: str) -> None:
    _store[phone_number] = chat_id
    _save()


def delete_chat_id(phone_number: str) -> None:
    _store.pop(phone_number, None)
    _save()


def load() -> None:
    """Load the chat store from disk. Safe to call at startup."""
    global _store
    if _store_path.exists():
        try:
            _store = json.loads(_store_path.read_text())
            logger.info("Loaded %d chat mappings from %s", len(_store), _store_path)
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to load chat store from %s, starting fresh", _store_path)
            _store = {}
    else:
        _store = {}


def _save() -> None:
    try:
        _store_path.write_text(json.dumps(_store, indent=2))
    except OSError:
        logger.warning("Failed to persist chat store to %s", _store_path)
