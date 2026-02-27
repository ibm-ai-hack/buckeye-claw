from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v3/recsports"


@tool
async def get_recsports_facilities() -> StringToolOutput:
    """Get all OSU recreation sports facilities with hours and availability."""
    data = await fetch_json(BASE_URL)
    return StringToolOutput(format_response(data, "Rec Sports Facilities"))


@tool
async def search_recsports_facilities(query: str) -> StringToolOutput:
    """Search rec sports facilities by name or abbreviation."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            f for f in items
            if q in str(f.get("title", "")).lower() or q in str(f.get("abbreviation", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Facilities matching '{query}'"))
    return StringToolOutput(format_response(data, f"Facilities matching '{query}'"))


@tool
async def get_facility_hours() -> StringToolOutput:
    """Get current operating hours for all rec sports facilities."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        hours_info = [
            {"name": f.get("title"), "hours": f.get("hours"), "isOpen": f.get("isOpen")}
            for f in items
        ]
        return StringToolOutput(format_response(hours_info, "Facility Hours"))
    return StringToolOutput(format_response(data, "Facility Hours"))


@tool
async def get_facility_events(facility_id: str = "") -> StringToolOutput:
    """Get scheduled events at rec sports facilities. Optionally filter by facility ID."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        events = []
        for f in items:
            facility_events = f.get("events", [])
            if facility_id and str(f.get("id", "")) != facility_id:
                continue
            for e in facility_events:
                e["facility"] = f.get("title")
                events.append(e)
        return StringToolOutput(format_response(events, "Facility Events"))
    return StringToolOutput(format_response(data, "Facility Events"))
