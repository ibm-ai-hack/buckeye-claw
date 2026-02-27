from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/foodtruck"


@tool
async def get_foodtruck_events() -> StringToolOutput:
    """Get all campus food truck events and schedules."""
    data = await fetch_json(f"{BASE_URL}/events")
    return StringToolOutput(format_response(data, "Food Truck Events"))


@tool
async def search_foodtrucks(query: str) -> StringToolOutput:
    """Search food trucks by name or cuisine type."""
    data = await fetch_json(f"{BASE_URL}/events")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            e for e in items
            if q in str(e.get("name", "")).lower()
            or any(q in str(c).lower() for c in e.get("cuisine", []))
        ]
        return StringToolOutput(format_response(filtered, f"Food trucks matching '{query}'"))
    return StringToolOutput(format_response(data, f"Food trucks matching '{query}'"))


@tool
async def get_foodtrucks_by_location(location: str) -> StringToolOutput:
    """Find food trucks at a specific campus location."""
    data = await fetch_json(f"{BASE_URL}/events")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = location.lower()
        filtered = [
            e for e in items
            if q in str(e.get("location", {}).get("address", "")).lower()
            or q in str(e.get("location", {}).get("name", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Food trucks at '{location}'"))
    return StringToolOutput(format_response(data, f"Food trucks at '{location}'"))
