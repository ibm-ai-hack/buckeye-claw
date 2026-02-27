from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/library"
ROOMS_URL = f"{BASE_URL}/roomreservation/api/v1/rooms"

AMENITIES = ["whiteboard", "HDTV", "video conferencing", "computer", "projector"]


@tool
async def get_library_locations() -> StringToolOutput:
    """Get all OSU library locations with addresses, hours, and contact info."""
    data = await fetch_json(f"{BASE_URL}/locations")
    return StringToolOutput(format_response(data, "Library Locations"))


@tool
async def search_library_locations(query: str) -> StringToolOutput:
    """Search for a library location by name."""
    data = await fetch_json(f"{BASE_URL}/locations")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [loc for loc in items if q in str(loc.get("name", "")).lower()]
        return StringToolOutput(format_response(filtered, f"Libraries matching '{query}'"))
    return StringToolOutput(format_response(data, f"Libraries matching '{query}'"))


@tool
async def get_library_rooms() -> StringToolOutput:
    """Get all available library study rooms for reservation."""
    data = await fetch_json(ROOMS_URL)
    return StringToolOutput(format_response(data, "Library Study Rooms"))


@tool
async def search_library_rooms(query: str) -> StringToolOutput:
    """Search for library study rooms by name or location."""
    data = await fetch_json(ROOMS_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            r for r in items
            if q in str(r.get("name", "")).lower() or q in str(r.get("location", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Rooms matching '{query}'"))
    return StringToolOutput(format_response(data, f"Rooms matching '{query}'"))


@tool
async def get_rooms_by_capacity(min_capacity: int, max_capacity: int = 0) -> StringToolOutput:
    """Find library rooms by capacity. Provide minimum capacity; max is optional."""
    data = await fetch_json(ROOMS_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        filtered = [
            r for r in items
            if r.get("capacity", 0) >= min_capacity
            and (max_capacity == 0 or r.get("capacity", 0) <= max_capacity)
        ]
        return StringToolOutput(format_response(filtered, f"Rooms with capacity >= {min_capacity}"))
    return StringToolOutput(format_response(data, "Library Rooms"))


@tool
async def get_rooms_with_amenities(amenity: str) -> StringToolOutput:
    """Find library rooms with a specific amenity. Options: whiteboard, HDTV, video conferencing, computer, projector."""
    if amenity.lower() not in [a.lower() for a in AMENITIES]:
        return StringToolOutput(f"Unknown amenity '{amenity}'. Options: {', '.join(AMENITIES)}")
    data = await fetch_json(ROOMS_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        a = amenity.lower()
        filtered = [
            r for r in items
            if any(a in str(am).lower() for am in r.get("amenities", []))
        ]
        return StringToolOutput(format_response(filtered, f"Rooms with {amenity}"))
    return StringToolOutput(format_response(data, f"Rooms with {amenity}"))
