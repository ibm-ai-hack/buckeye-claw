import json
import logging

from beeai_framework.tools import StringToolOutput, tool

logger = logging.getLogger(__name__)


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
    """Get the menu for a Grubhub restaurant. Search for the restaurant first."""
    try:
        from grubhub.automation import get_driver, search_restaurants, get_menu
        driver = get_driver()
        search_restaurants(driver, restaurant_name)
        menu = get_menu(driver, restaurant_index=0)
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
    """Place a Grubhub order. Provide the restaurant name and comma-separated item names.

    Args:
        restaurant_name: Name of the restaurant to order from.
        items: Comma-separated list of menu item names to add to cart.
    """
    try:
        from grubhub.automation import get_driver, search_restaurants, get_menu, add_to_cart, checkout
        driver = get_driver()
        search_restaurants(driver, restaurant_name)
        get_menu(driver, restaurant_index=0)

        item_list = [i.strip() for i in items.split(",")]
        added = []
        failed = []
        for item_name in item_list:
            if add_to_cart(driver, item_name):
                added.append(item_name)
            else:
                failed.append(item_name)

        result = checkout(driver)
        driver.quit()

        msg = f"Order from {restaurant_name}:\n"
        if added:
            msg += f"Added: {', '.join(added)}\n"
        if failed:
            msg += f"Could not add: {', '.join(failed)}\n"
        msg += result
        return StringToolOutput(msg)
    except Exception as e:
        logger.exception("Grubhub order failed")
        return StringToolOutput(f"Grubhub ordering unavailable: {type(e).__name__}.")
