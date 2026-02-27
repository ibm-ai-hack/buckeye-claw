from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v3/athletics"


@tool
async def get_athletics_all() -> StringToolOutput:
    """Get info about all OSU athletics programs and schedules."""
    data = await fetch_json(f"{BASE_URL}/all")
    return StringToolOutput(format_response(data, "Athletics Programs"))


@tool
async def search_sports(query: str) -> StringToolOutput:
    """Search for a specific sport or team by name."""
    data = await fetch_json(f"{BASE_URL}/all")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            s for s in items
            if q in str(s.get("title", "")).lower() or q in str(s.get("abbreviation", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Sports matching '{query}'"))
    return StringToolOutput(format_response(data, f"Sports matching '{query}'"))


@tool
async def get_sport_by_gender(gender: str) -> StringToolOutput:
    """Filter sports programs by gender: men, women, or mixed."""
    data = await fetch_json(f"{BASE_URL}/all")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        g = gender.lower()
        filtered = [s for s in items if str(s.get("gender", "")).lower() == g]
        return StringToolOutput(format_response(filtered, f"{gender.capitalize()} sports"))
    return StringToolOutput(format_response(data, f"{gender.capitalize()} sports"))


@tool
async def get_upcoming_games(sport: str = "") -> StringToolOutput:
    """Get upcoming OSU athletic events. Optionally filter by sport name."""
    data = await fetch_json(f"{BASE_URL}/all")
    items = data.get("data", data) if isinstance(data, dict) else data
    events = []
    if isinstance(items, list):
        for s in items:
            if sport and sport.lower() not in str(s.get("title", "")).lower():
                continue
            for e in s.get("upcomingEvents", []):
                e["sport"] = s.get("title")
                events.append(e)
        events = events[:50]
    return StringToolOutput(format_response(events, "Upcoming Games"))
