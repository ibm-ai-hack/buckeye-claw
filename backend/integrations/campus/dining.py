import json

from beeai_framework.tools import StringToolOutput, tool

from .utils import fetch_json, now_eastern

BASE_URL = "https://content.osu.edu/v2/api/v1/dining/locations"


def _summarize_locations(data: dict | list) -> str:
    """Format dining locations concisely so all 35+ fit within token limits."""
    if isinstance(data, dict):
        locations = data.get("data", {}).get("locationsWithGeoCode", [])
    else:
        locations = data

    lines: list[str] = []
    for loc in locations:
        name = loc.get("locationName", "Unknown")
        style = (loc.get("diningStyle") or "").strip()
        building = (loc.get("address2") or "").strip().strip("()")
        address = (loc.get("address1") or "").strip()
        cuisines = [c.get("cuisineType", "") for c in (loc.get("cuisines") or [])]
        cuisine_str = ", ".join(cuisines) if cuisines else ""

        parts = [f"- {name}"]
        if building:
            parts.append(f"  building: {building}")
        if address:
            parts.append(f"  address: {address}")
        if style:
            parts.append(f"  type: {style}")
        if cuisine_str:
            parts.append(f"  cuisines: {cuisine_str}")

        lines.append("\n".join(parts))

    return "\n".join(lines)


@tool
async def get_dining_locations() -> StringToolOutput:
    """Get all OSU dining locations with their type, building, and cuisines.
    Returns a concise summary of every campus dining location."""
    data = await fetch_json(BASE_URL)
    timestamp = now_eastern()
    summary = _summarize_locations(data)
    return StringToolOutput(f"All OSU Dining Locations (retrieved {timestamp}):\n\n{summary}")


@tool
async def search_dining_locations(query: str) -> StringToolOutput:
    """Search OSU dining locations by name, building, cuisine, or style.
    Use this to find a specific dining hall, cafe, or restaurant on campus.
    Examples: 'Scott', 'Kennedy', 'Sloopy', 'coffee', 'marketplace', 'traditions'."""
    data = await fetch_json(BASE_URL)
    locations = data.get("data", {}).get("locationsWithGeoCode", [])
    q = query.lower()

    matches = []
    for loc in locations:
        searchable = " ".join(filter(None, [
            loc.get("locationName") or "",
            loc.get("address1") or "",
            loc.get("address2") or "",
            loc.get("diningStyle") or "",
            loc.get("summary") or "",
            " ".join(c.get("cuisineType", "") for c in (loc.get("cuisines") or [])),
        ])).lower()

        if q in searchable:
            matches.append(loc)

    timestamp = now_eastern()
    if not matches:
        return StringToolOutput(
            f"No dining locations matched '{query}' (searched {timestamp}). "
            f"Try a broader term like 'traditions', 'cafe', 'marketplace', or 'coffee'."
        )

    # Return detailed info for matches
    results: list[str] = []
    for loc in matches:
        name = loc.get("locationName", "Unknown")
        style = (loc.get("diningStyle") or "").strip()
        building = (loc.get("address2") or "").strip().strip("()")
        address = (loc.get("address1") or "").strip()
        summary = (loc.get("summary") or "").strip()
        cuisines = [c.get("cuisineType", "") for c in (loc.get("cuisines") or [])]
        cuisine_str = ", ".join(cuisines) if cuisines else ""

        parts = [f"-- {name} --"]
        if building:
            parts.append(f"  Building: {building}")
        if address:
            parts.append(f"  Address: {address}")
        if style:
            parts.append(f"  Type: {style}")
        if cuisine_str:
            parts.append(f"  Cuisines: {cuisine_str}")
        if summary:
            # Strip HTML and truncate
            clean_summary = summary.replace("&lsquo;", "'").replace("&rsquo;", "'")
            clean_summary = clean_summary[:300]
            parts.append(f"  Info: {clean_summary}")

        results.append("\n".join(parts))

    return StringToolOutput(
        f"Dining locations matching '{query}' ({len(matches)} found, retrieved {timestamp}):\n\n"
        + "\n\n".join(results)
    )


@tool
async def get_dining_locations_with_menus() -> StringToolOutput:
    """Get OSU dining locations including menu section details.
    Use this to find what food is available and get section IDs for detailed menus."""
    data = await fetch_json(f"{BASE_URL}?menus=true")
    locations = data.get("data", {}).get("locationsWithGeoCode", [])
    timestamp = now_eastern()

    lines: list[str] = []
    for loc in locations:
        name = loc.get("locationName", "Unknown")
        menus = loc.get("locationMenu", [])
        if not menus:
            continue

        lines.append(f"-- {name} --")
        for menu in menus:
            menu_name = menu.get("menuName", "")
            sections = menu.get("menuSections", [])
            if sections:
                lines.append(f"  Menu: {menu_name}")
                for sec in sections:
                    sec_name = sec.get("sectionName", "")
                    sec_id = sec.get("sectionID", "")
                    lines.append(f"    - {sec_name} (section_id: {sec_id})")

    if not lines:
        return StringToolOutput(f"No menus currently available (retrieved {timestamp}).")

    result = "\n".join(lines)
    if len(result) > 6000:
        result = result[:6000] + "\n... (truncated, use search_dining_locations for specific locations)"

    return StringToolOutput(f"OSU Dining Menus (retrieved {timestamp}):\n\n{result}")


@tool
async def get_dining_menu(section_id: int) -> StringToolOutput:
    """Get detailed menu items for a specific dining section.
    Use get_dining_locations_with_menus or search_dining_locations first to find section IDs."""
    data = await fetch_json(f"https://content.osu.edu/v2/api/v1/dining/menu/{section_id}")
    timestamp = now_eastern()

    # Format menu items concisely
    items = data if isinstance(data, list) else data.get("data", data)
    if isinstance(items, dict):
        items = items.get("menuItems", [items])

    result = json.dumps(items, indent=2, default=str)
    if len(result) > 6000:
        result = result[:6000] + "\n... (truncated)"

    return StringToolOutput(f"Menu for Section {section_id} (retrieved {timestamp}):\n{result}")
