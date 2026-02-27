from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/student-org"


@tool
async def get_student_organizations() -> StringToolOutput:
    """Get all OSU student organizations."""
    data = await fetch_json(f"{BASE_URL}/all")
    return StringToolOutput(format_response(data, "Student Organizations"))


@tool
async def search_student_orgs(query: str) -> StringToolOutput:
    """Search student organizations by name or keyword."""
    data = await fetch_json(f"{BASE_URL}/all")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            o for o in items
            if q in str(o.get("name", "")).lower()
            or q in str(o.get("purposeStatement", "")).lower()
            or any(q in str(k).lower() for k in o.get("keywords", []))
        ]
        return StringToolOutput(format_response(filtered, f"Orgs matching '{query}'"))
    return StringToolOutput(format_response(data, f"Orgs matching '{query}'"))


@tool
async def get_orgs_by_type(org_type: str) -> StringToolOutput:
    """Filter student organizations by type/category."""
    data = await fetch_json(f"{BASE_URL}/all")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = org_type.lower()
        filtered = [
            o for o in items
            if q in str(o.get("makeUp", "")).lower()
            or q in str(o.get("secondaryMakeUp", "")).lower()
        ]
        return StringToolOutput(format_response(filtered, f"Orgs of type '{org_type}'"))
    return StringToolOutput(format_response(data, f"Orgs of type '{org_type}'"))


@tool
async def get_orgs_by_career_level(career_level: str) -> StringToolOutput:
    """Filter student organizations by career level: undergraduate, graduate, or professional."""
    data = await fetch_json(f"{BASE_URL}/all")
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = career_level.lower()
        filtered = [o for o in items if q in str(o.get("career", "")).lower()]
        return StringToolOutput(format_response(filtered, f"{career_level.capitalize()} organizations"))
    return StringToolOutput(format_response(data, f"{career_level.capitalize()} organizations"))
