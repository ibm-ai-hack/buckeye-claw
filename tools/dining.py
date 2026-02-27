from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/api/v1/dining"


@tool
async def get_dining_locations() -> StringToolOutput:
    """Get all OSU dining locations with hours and availability."""
    data = await fetch_json(BASE_URL)
    return StringToolOutput(format_response(data, "Dining Locations"))


@tool
async def get_dining_locations_with_menus() -> StringToolOutput:
    """Get OSU dining locations including menu section details."""
    data = await fetch_json(f"{BASE_URL}?menus=true")
    return StringToolOutput(format_response(data, "Dining Locations with Menus"))


@tool
async def get_dining_menu(section_id: int) -> StringToolOutput:
    """Get detailed menu items for a specific dining section. Use get_dining_locations_with_menus first to find section IDs."""
    data = await fetch_json(f"{BASE_URL}/menu/{section_id}")
    return StringToolOutput(format_response(data, f"Menu for Section {section_id}"))
