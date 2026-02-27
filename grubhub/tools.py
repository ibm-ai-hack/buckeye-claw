import logging

from beeai_framework.tools import StringToolOutput, tool

logger = logging.getLogger(__name__)


# ── Scheduled ordering tools ───────────────────────────────────────────


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
    try:
        from grubhub.scheduler import schedule_order, parse_time

        run_at = parse_time(time_description)
        job_id = schedule_order(restaurant_name, items, run_at, from_number)
        return StringToolOutput(
            f"Got it! I'll order {items} from {restaurant_name} at "
            f"{run_at.strftime('%I:%M %p')} and text you when it's done. "
            f"(Order ID: {job_id})"
        )
    except ValueError as e:
        return StringToolOutput(f"Couldn't understand the time: {e}")
    except Exception as e:
        logger.exception("Failed to schedule Grubhub order")
        return StringToolOutput(f"Failed to schedule order: {type(e).__name__}.")


@tool
async def list_scheduled_grubhub_orders(from_number: str) -> StringToolOutput:
    """List pending scheduled Grubhub orders for the caller.

    Args:
        from_number: The caller's phone number (from the [caller: ...] prefix).
    """
    from grubhub.scheduler import get_scheduled_orders

    orders = get_scheduled_orders(from_number)
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
    from grubhub.scheduler import cancel_order

    if cancel_order(job_id):
        return StringToolOutput(f"Cancelled scheduled order {job_id}.")
    return StringToolOutput(f"No scheduled order found with ID {job_id}.")


@tool
async def search_grubhub_restaurants(query: str) -> StringToolOutput:
    """Search for restaurants on Grubhub. Requires Android emulator running with Grubhub installed."""
    try:
        from grubhub.automation import get_driver, search_restaurants
        driver = get_driver()
        results = search_restaurants(driver, query)
        driver.quit()
        if results:
            lines = [f"- {r['name']}" for r in results]
            return StringToolOutput(f"Grubhub restaurants for '{query}':\n" + "\n".join(lines))
        return StringToolOutput(f"No restaurants found for '{query}' on Grubhub.")
    except Exception as e:
        logger.exception("Grubhub search failed")
        return StringToolOutput(
            f"Grubhub search unavailable: {type(e).__name__}. "
            "Make sure the Android emulator is running with Grubhub installed and Appium server is started."
        )


@tool
async def get_restaurant_menu(restaurant_name: str) -> StringToolOutput:
    """Get the menu for a Grubhub restaurant. Intelligently finds the right
    restaurant from search results using LLM matching."""
    try:
        from grubhub.automation import get_driver, search_restaurants, select_restaurant
        driver = get_driver()
        results = search_restaurants(driver, restaurant_name)
        if not results:
            driver.quit()
            return StringToolOutput(f"No restaurants found for '{restaurant_name}'.")
        menu = select_restaurant(driver, restaurant_name, results)
        driver.quit()
        if menu:
            lines = [f"- {item['name']}" for item in menu]
            return StringToolOutput(f"Menu for '{restaurant_name}':\n" + "\n".join(lines))
        return StringToolOutput(f"Could not load menu for '{restaurant_name}'.")
    except Exception as e:
        logger.exception("Grubhub menu failed")
        return StringToolOutput(f"Grubhub menu unavailable: {type(e).__name__}.")


@tool
async def place_grubhub_order(restaurant_name: str, items: str) -> StringToolOutput:
    """Place a Grubhub order. Uses LLM intelligence to match the restaurant
    and menu items to what the user actually wants.

    Args:
        restaurant_name: Name of the restaurant to order from.
        items: Comma-separated list of menu item names to add to cart.
    """
    try:
        from grubhub.automation import get_driver, intelligent_order
        driver = get_driver()
        result = intelligent_order(driver, restaurant_name, items)
        driver.quit()

        msg = f"Order from {restaurant_name}:\n"
        if result["added"]:
            msg += f"Added: {', '.join(result['added'])}\n"
        if result["failed"]:
            msg += f"Could not add: {', '.join(result['failed'])}\n"
        msg += result["checkout_result"]
        return StringToolOutput(msg)
    except Exception as e:
        logger.exception("Grubhub order failed")
        return StringToolOutput(f"Grubhub ordering unavailable: {type(e).__name__}.")
