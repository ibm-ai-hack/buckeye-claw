from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/merchants"


@tool
async def get_buckid_merchants() -> StringToolOutput:
    """Get all merchants that accept BuckID payments."""
    data = await fetch_json(BASE_URL)
    return StringToolOutput(format_response(data, "BuckID Merchants"))


@tool
async def search_merchants(query: str) -> StringToolOutput:
    """Search BuckID merchants by name or category."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = query.lower()
        filtered = [
            m for m in items
            if q in str(m.get("title", "")).lower()
            or any(q in str(c).lower() for c in m.get("categories", []))
        ]
        return StringToolOutput(format_response(filtered, f"Merchants matching '{query}'"))
    return StringToolOutput(format_response(data, f"Merchants matching '{query}'"))


@tool
async def get_merchants_by_food_type(food_type: str) -> StringToolOutput:
    """Find merchants by cuisine/food type (e.g., pizza, sushi, coffee)."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        q = food_type.lower()
        filtered = [
            m for m in items
            if any(q in str(ft).lower() for ft in m.get("foodTypes", []))
        ]
        return StringToolOutput(format_response(filtered, f"Merchants with {food_type}"))
    return StringToolOutput(format_response(data, f"Merchants with {food_type}"))


@tool
async def get_merchants_with_meal_plan() -> StringToolOutput:
    """Get merchants that accept OSU meal plan payments."""
    data = await fetch_json(BASE_URL)
    items = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(items, list):
        filtered = [m for m in items if m.get("hasMealPlan")]
        return StringToolOutput(format_response(filtered, "Meal Plan Merchants"))
    return StringToolOutput(format_response(data, "Meal Plan Merchants"))
