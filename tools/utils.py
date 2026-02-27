import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx

EASTERN = ZoneInfo("America/New_York")

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=15.0)
    return _client


async def fetch_json(url: str) -> dict | list:
    client = await get_client()
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.json()


def to_eastern(utc_str: str) -> str:
    try:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                dt = datetime.strptime(utc_str, fmt)
                break
            except ValueError:
                continue
        else:
            return utc_str
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        eastern = dt.astimezone(EASTERN)
        return eastern.strftime("%B %d, %Y %I:%M %p ET")
    except Exception:
        return utc_str


def now_eastern() -> str:
    return datetime.now(EASTERN).strftime("%B %d, %Y %I:%M %p ET")


def format_response(data: dict | list, label: str = "Results") -> str:
    timestamp = now_eastern()
    text = json.dumps(data, indent=2, default=str)
    # Truncate very long responses for SMS friendliness
    if len(text) > 8000:
        text = text[:8000] + "\n... (truncated)"
    return f"{label} (retrieved {timestamp}):\n{text}"
