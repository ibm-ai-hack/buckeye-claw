from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/api/buildings"

ROOM_TYPES = ["lactation", "sanctuary", "wellness", "gender_inclusive_restroom"]


@tool
async def get_buildings() -> StringToolOutput:
    """Get all OSU buildings with addresses, locations, departments, and room details."""
    data = await fetch_json(BASE_URL)
    return StringToolOutput(format_response(data, "Campus Buildings"))


@tool
async def search_buildings(query: str) -> StringToolOutput:
    """Search for campus buildings by name or building number."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            b for b in items
            if q in str(b.get("name", "")).lower()
            or q in str(b.get("buildingNumber", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Buildings matching '{query}'"))
    return StringToolOutput(format_response(data, f"Buildings matching '{query}'"))


@tool
async def get_building_details(building_number: str) -> StringToolOutput:
    """Get detailed info about a specific building including rooms and departments."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        building = next((b for b in items if str(b.get("buildingNumber", "")) == building_number), None)
        if building:
            return StringToolOutput(format_response(building, f"Building {building_number}"))
        return StringToolOutput(f"Building number '{building_number}' not found.")
    return StringToolOutput(format_response(data, f"Building {building_number}"))


@tool
async def find_room_type(room_type: str) -> StringToolOutput:
    """Find buildings with a specific room type: lactation, sanctuary, wellness, or gender_inclusive_restroom."""
    if room_type not in ROOM_TYPES:
        return StringToolOutput(f"Unknown room type '{room_type}'. Options: {', '.join(ROOM_TYPES)}")
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        filtered = [
            b for b in items
            if any(room_type in str(r.get("type", "")).lower() for r in b.get("rooms", []))
        ]
        return StringToolOutput(format_response(filtered, f"Buildings with {room_type} rooms"))
    return StringToolOutput(format_response(data, f"Buildings with {room_type} rooms"))
