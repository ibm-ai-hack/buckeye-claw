from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/calendar"


@tool
async def get_academic_calendar() -> StringToolOutput:
    """Get the OSU academic calendar with important dates (semesters, breaks, deadlines)."""
    data = await fetch_json(f"{BASE_URL}/academic")
    return StringToolOutput(format_response(data, "Academic Calendar"))


@tool
async def get_university_holidays() -> StringToolOutput:
    """Get OSU university holidays."""
    data = await fetch_json(f"{BASE_URL}/holidays")
    return StringToolOutput(format_response(data, "University Holidays"))


@tool
async def search_calendar_events(query: str) -> StringToolOutput:
    """Search the academic calendar for specific events by keyword."""
    data = await fetch_json(f"{BASE_URL}/academic")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            e for e in items
            if q in str(e.get("title", "")).lower()
            or q in str(e.get("text", "")).lower()
            or q in str(e.get("description", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Calendar events matching '{query}'"))
    return StringToolOutput(format_response(data, f"Calendar events matching '{query}'"))
