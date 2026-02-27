from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/events"


@tool
async def get_campus_events() -> StringToolOutput:
    """Get all upcoming OSU campus events."""
    data = await fetch_json(BASE_URL)
    return StringToolOutput(format_response(data, "Campus Events"))


@tool
async def search_campus_events(query: str) -> StringToolOutput:
    """Search campus events by title or description keyword."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            e for e in items
            if q in str(e.get("title", "")).lower()
            or q in str(e.get("description", "")).lower()
            or q in str(e.get("content", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Events matching '{query}'"))
    return StringToolOutput(format_response(data, f"Events matching '{query}'"))


@tool
async def get_events_by_date_range(start_date: str, end_date: str) -> StringToolOutput:
    """Get campus events within a date range. Dates should be YYYY-MM-DD format."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        filtered = [
            e for e in items
            if _date_in_range(e, start_date, end_date)
        ]
        return StringToolOutput(format_response(filtered, f"Events from {start_date} to {end_date}"))
    return StringToolOutput(format_response(data, f"Events from {start_date} to {end_date}"))


def _date_in_range(event: dict, start: str, end: str) -> bool:
    event_date = str(event.get("startDate", event.get("date", "")))[:10]
    if not event_date:
        return False
    return start <= event_date <= end
