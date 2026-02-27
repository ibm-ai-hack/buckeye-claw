from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/parking/garages"


@tool
async def get_parking_availability() -> StringToolOutput:
    """Get real-time parking availability for all OSU parking garages."""
    data = await fetch_json(f"{BASE_URL}/availability")
    return StringToolOutput(format_response(data, "Parking Availability"))
