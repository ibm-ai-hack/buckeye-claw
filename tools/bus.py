from beeai_framework.tools import StringToolOutput, tool

from tools.utils import fetch_json, format_response

BASE_URL = "https://content.osu.edu/v2/bus"

BUS_ROUTES = {
    "ACK": "Ackerman Shuttle",
    "BE": "Buckeye Express",
    "CC": "Campus Connector",
    "CLS": "Campus Loop South",
    "ER": "East Residential",
    "MC": "Medical Center",
    "MM": "Morehouse to Med Center",
    "NWC": "Northwest Connector",
    "WMC": "Wexner Medical Center",
}


@tool
async def get_bus_routes() -> StringToolOutput:
    """Get all OSU CABS bus routes and their codes. Available routes: ACK, BE, CC, CLS, ER, MC, MM, NWC, WMC."""
    data = await fetch_json(f"{BASE_URL}/routes/")
    return StringToolOutput(format_response(data, "Bus Routes"))


@tool
async def get_bus_stops(route_code: str) -> StringToolOutput:
    """Get all stops for a specific bus route. Route codes: ACK, BE, CC, CLS, ER, MC, MM, NWC, WMC."""
    route_code = route_code.upper()
    if route_code not in BUS_ROUTES:
        return StringToolOutput(f"Invalid route code '{route_code}'. Valid codes: {', '.join(BUS_ROUTES.keys())}")
    data = await fetch_json(f"{BASE_URL}/routes/{route_code}")
    return StringToolOutput(format_response(data, f"Stops for {BUS_ROUTES[route_code]}"))


@tool
async def get_bus_vehicles(route_code: str) -> StringToolOutput:
    """Get real-time vehicle positions for a bus route. Route codes: ACK, BE, CC, CLS, ER, MC, MM, NWC, WMC."""
    route_code = route_code.upper()
    if route_code not in BUS_ROUTES:
        return StringToolOutput(f"Invalid route code '{route_code}'. Valid codes: {', '.join(BUS_ROUTES.keys())}")
    data = await fetch_json(f"{BASE_URL}/routes/{route_code}/vehicles")
    return StringToolOutput(format_response(data, f"Vehicles on {BUS_ROUTES[route_code]}"))
