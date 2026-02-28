"""
Grubhub tools for the BeeAI agent — thin HTTP clients that call the
local Grubhub server (exposed via ngrok).

Tool signatures are unchanged so agents/factories.py and
agents/orchestrator.py require no modifications.
"""

import logging
import os

import httpx
from beeai_framework.tools import StringToolOutput, tool

logger = logging.getLogger(__name__)

_TIMEOUT_LONG = 120.0  # Appium operations can take 30-60s
_TIMEOUT_SHORT = 30.0


# ── HTTP helpers ──────────────────────────────────────────────────────


def _server_url() -> str:
    url = os.environ.get("GRUBHUB_SERVER_URL", "")
    if not url:
        raise RuntimeError("GRUBHUB_SERVER_URL is not set")
    return url.rstrip("/")


def _headers() -> dict:
    return {"X-Grubhub-Server-Key": os.environ.get("GRUBHUB_SERVER_KEY", "")}


def _post(path: str, body: dict, timeout: float = _TIMEOUT_LONG) -> dict:
    try:
        resp = httpx.post(
            f"{_server_url()}{path}", json=body, headers=_headers(), timeout=timeout
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Grubhub server is not reachable. The local server or ngrok tunnel may be down."}
    except httpx.TimeoutException:
        return {"success": False, "error": "Grubhub server timed out. The automation may be stuck."}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"success": False, "error": "Grubhub server rejected the request. Check GRUBHUB_SERVER_KEY."}
        return {"success": False, "error": f"Grubhub server error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Grubhub request failed: {type(e).__name__}: {e}"}


def _get(path: str, params: dict | None = None) -> dict:
    try:
        resp = httpx.get(
            f"{_server_url()}{path}", params=params, headers=_headers(), timeout=_TIMEOUT_SHORT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Grubhub server is not reachable."}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"success": False, "error": "Grubhub server rejected the request. Check GRUBHUB_SERVER_KEY."}
        return {"success": False, "error": f"Grubhub server error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Grubhub request failed: {type(e).__name__}: {e}"}


def _delete(path: str) -> dict:
    try:
        resp = httpx.delete(
            f"{_server_url()}{path}", headers=_headers(), timeout=_TIMEOUT_SHORT
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Grubhub server is not reachable."}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"success": False, "error": "Grubhub server rejected the request. Check GRUBHUB_SERVER_KEY."}
        return {"success": False, "error": f"Grubhub server error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Grubhub request failed: {type(e).__name__}: {e}"}


def _unavailable(result: dict, context: str) -> StringToolOutput:
    return StringToolOutput(
        f"Grubhub {context} unavailable: {result.get('error', 'Unknown error')}. "
        "The Grubhub server may be offline."
    )


# ── Scheduled ordering tools ─────────────────────────────────────────


@tool
async def schedule_grubhub_order(
    restaurant_name: str, items: str, time_description: str, from_number: str
) -> StringToolOutput:
    """Schedule a Grubhub order for a future time. The order will be placed
    automatically and the user will be notified via text.

    Args:
        restaurant_name: Name of the restaurant to order from.
        items: Comma-separated list of menu item names.
        time_description: When to place the order, e.g. "6pm", "6:30 PM", "in 2 hours".
        from_number: The caller's phone number (from the [caller: ...] prefix).
    """
    result = _post("/api/grubhub/schedule", {
        "restaurant_name": restaurant_name,
        "items": items,
        "time_description": time_description,
        "from_number": from_number,
    })
    if not result.get("success"):
        return _unavailable(result, "scheduling")
    data = result["data"]
    return StringToolOutput(
        f"Got it! I'll order {items} from {restaurant_name} at "
        f"{data['run_at']} and text you when it's done. "
        f"(Order ID: {data['job_id']})"
    )


@tool
async def list_scheduled_grubhub_orders(from_number: str) -> StringToolOutput:
    """List pending scheduled Grubhub orders for the caller.

    Args:
        from_number: The caller's phone number (from the [caller: ...] prefix).
    """
    result = _get("/api/grubhub/scheduled", {"from_number": from_number})
    if not result.get("success"):
        return _unavailable(result, "schedule listing")
    orders = result["data"]["orders"]
    if not orders:
        return StringToolOutput("You have no scheduled Grubhub orders.")
    lines = [
        f"- {o['items']} from {o['restaurant']} at {o['scheduled_time']} (ID: {o['job_id']})"
        for o in orders
    ]
    return StringToolOutput("Your scheduled orders:\n" + "\n".join(lines))


@tool
async def cancel_scheduled_grubhub_order(job_id: str) -> StringToolOutput:
    """Cancel a scheduled Grubhub order by its order ID.

    Args:
        job_id: The order ID returned when the order was scheduled.
    """
    result = _delete(f"/api/grubhub/scheduled/{job_id}")
    if not result.get("success"):
        error = result.get("error", "")
        if "No scheduled order" in error:
            return StringToolOutput(f"No scheduled order found with ID {job_id}.")
        return _unavailable(result, "cancellation")
    return StringToolOutput(f"Cancelled scheduled order {job_id}.")


# ── Live ordering tools ───────────────────────────────────────────────


@tool
async def search_grubhub_restaurants(query: str) -> StringToolOutput:
    """Search for restaurants on Grubhub. Requires the Grubhub local server to be running."""
    result = _post("/api/grubhub/search", {"query": query})
    if not result.get("success"):
        return _unavailable(result, "search")
    restaurants = result["data"]["restaurants"]
    if restaurants:
        lines = [f"- {r['name']}" for r in restaurants]
        return StringToolOutput(f"Grubhub restaurants for '{query}':\n" + "\n".join(lines))
    return StringToolOutput(f"No restaurants found for '{query}' on Grubhub.")


@tool
async def get_restaurant_menu(restaurant_name: str) -> StringToolOutput:
    """Get the menu for a Grubhub restaurant. Intelligently finds the right
    restaurant from search results using LLM matching."""
    result = _post("/api/grubhub/menu", {"restaurant_name": restaurant_name})
    if not result.get("success"):
        return _unavailable(result, "menu")
    menu_items = result["data"]["menu"]
    if menu_items:
        lines = [f"- {item['name']}" for item in menu_items]
        return StringToolOutput(f"Menu for '{restaurant_name}':\n" + "\n".join(lines))
    return StringToolOutput(f"Could not load menu for '{restaurant_name}'.")


@tool
async def place_grubhub_order(restaurant_name: str, items: str) -> StringToolOutput:
    """Place a Grubhub order. Uses LLM intelligence to match the restaurant
    and menu items to what the user actually wants.

    Args:
        restaurant_name: Name of the restaurant to order from.
        items: Comma-separated list of menu item names to add to cart.
    """
    result = _post("/api/grubhub/order", {
        "restaurant_name": restaurant_name,
        "items": items,
    })
    if not result.get("success"):
        return _unavailable(result, "ordering")
    data = result["data"]
    msg = f"Order from {restaurant_name}:\n"
    if data.get("added"):
        msg += f"Added: {', '.join(data['added'])}\n"
    if data.get("failed"):
        msg += f"Could not add: {', '.join(data['failed'])}\n"
    msg += data.get("checkout_result", "")
    return StringToolOutput(msg)
