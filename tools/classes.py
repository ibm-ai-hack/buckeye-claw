from urllib.parse import urlencode

from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/classes/search"


@tool
async def search_classes(
    query: str,
    term: str = "",
    campus: str = "",
    subject: str = "",
    academic_career: str = "",
    component: str = "",
    page: int = 1,
) -> StringToolOutput:
    """Search for OSU classes by keyword, subject, instructor, etc.

    Args:
        query: Search term (course title, subject, instructor name, or building).
        term: Four-digit term code (e.g., 1252 for Spring 2025). Optional.
        campus: Campus code — COL (Columbus), LMA (Lima), MNS (Mansfield), MRN (Marion), NWK (Newark). Optional.
        subject: Department code like CSE, MATH, ENGLISH. Optional.
        academic_career: Level — UGRD, GRAD, LAW, MED, DENT, VET. Optional.
        component: Class type — LEC, LAB, REC, SEM, IND. Optional.
        page: Page number for results (default 1).
    """
    params = {"q": query, "p": str(page)}
    if term:
        params["term"] = term
    if campus:
        params["campus"] = campus.upper()
    if subject:
        params["subject"] = subject.upper()
    if academic_career:
        params["academic-career"] = academic_career.upper()
    if component:
        params["component"] = component.upper()

    url = f"{BASE_URL}?{urlencode(params)}"
    data = await fetch_json(url)
    return StringToolOutput(format_response(data, f"Classes matching '{query}'"))
