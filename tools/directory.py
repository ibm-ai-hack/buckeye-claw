from urllib.parse import urlencode

from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

SEARCH_URL = "https://content.osu.edu/v2/people/search"


@tool
async def search_people(firstname: str = "", lastname: str = "") -> StringToolOutput:
    """Search for people in the OSU directory by first and/or last name. At least one name is required."""
    if not firstname and not lastname:
        return StringToolOutput("Please provide at least a first name or last name to search.")
    params = {}
    if firstname:
        params["firstname"] = firstname
    if lastname:
        params["lastname"] = lastname
    url = f"{SEARCH_URL}?{urlencode(params)}"
    data = await fetch_json(url)
    return StringToolOutput(format_response(data, f"People search: {firstname} {lastname}".strip()))
