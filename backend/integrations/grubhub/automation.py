"""
Grubhub ordering automation via Appium + Android emulator.

This module drives the Grubhub app UI to search restaurants, browse menus,
and place orders. An LLM intelligence layer (grubhub.intelligence) makes
decisions between steps — picking the right restaurant from results, matching
menu items to what the user actually wants, etc.

Requires a running Android emulator with Grubhub installed
and an Appium server running locally.
"""

import logging
import time

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

GRUBHUB_PACKAGE = "com.grubhub.android"
APPIUM_URL = "http://localhost:4723"
MAIN_ACTIVITY = "com.grubhub.dinerapp.android.splash.SplashActivity"

# Strings that appear in search results but aren't restaurant names
_SEARCH_NOISE = {
    "Top results at OSU", "Top results off-campus", "See all",
    "OSU Dining", "Off-campus", "Delivery", "Pickup", "Sort",
}

# Noise that appears on menu/restaurant screens
_MENU_NOISE = {
    "Most popular", "Popular items", "See all", "Ratings", "Reviews",
    "Delivery", "Pickup", "Schedule", "Info", "Group order",
    "Most ordered", "Picked for you", "Show all", "Cafe",
    "The Ohio State University", "Home", "Offers", "Orders", "Account",
    "Smoothies and Juices",
}


def _read_screen_texts(driver: webdriver.Remote) -> list[str]:
    """Read all visible text elements from the current screen."""
    elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    return [el.text.strip() for el in elements if el.text and el.text.strip()]


def get_driver() -> webdriver.Remote:
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.app_package = GRUBHUB_PACKAGE
    options.app_activity = MAIN_ACTIVITY
    options.no_reset = True
    return webdriver.Remote(APPIUM_URL, options=options)


def search_restaurants(driver: webdriver.Remote, query: str) -> list[dict]:
    """Search for restaurants in the Grubhub app."""
    wait = WebDriverWait(driver, 15)

    # Tap the search bar ("Restaurants, dishes, grocery…")
    search_bar = wait.until(
        EC.presence_of_element_located(
            (AppiumBy.XPATH, '//*[contains(@text, "Restaurants, dishes")]')
        )
    )
    search_bar.click()
    time.sleep(1)

    # Type query
    search_field = wait.until(
        EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
    )
    search_field.clear()
    search_field.send_keys(query)
    time.sleep(3)

    # Collect results — filter out noise, autocomplete suggestions, and short strings
    results = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    restaurants = []
    seen = set()
    for el in results:
        text = el.text.strip()
        if (
            text
            and len(text) > 2
            and text not in _SEARCH_NOISE
            and "min" not in text
            and "mi" not in text.split()
            and "in line" not in text
            and "no results" not in text.lower()
            and not text.replace(".", "").isdigit()
            and text not in seen
        ):
            seen.add(text)
            restaurants.append({"name": text})
    return restaurants[:10]


def select_restaurant(
    driver: webdriver.Remote, restaurant_name: str, results: list[dict]
) -> list[dict]:
    """Intelligently select the right restaurant and open its menu.

    Uses the LLM to pick the best match from search results, taps it,
    waits for the menu to load, and returns menu items.
    """
    from backend.integrations.grubhub.intelligence import pick_restaurant

    # Ask the intelligence layer which result is the best match
    best_idx = pick_restaurant(restaurant_name, results)
    chosen = results[best_idx]["name"]
    logger.info("Selected restaurant: '%s' (index %d)", chosen, best_idx)

    # Tap the matching restaurant by its text
    wait = WebDriverWait(driver, 10)
    try:
        restaurant_el = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, f'//*[contains(@text, "{chosen}")]')
            )
        )
        restaurant_el.click()
    except Exception:
        # Fall back to tapping by position in the clickable list
        logger.warning("Could not find '%s' by text, trying clickable cards", chosen)
        cards = driver.find_elements(
            AppiumBy.XPATH,
            '//android.view.ViewGroup[@clickable="true"]',
        )
        # Skip the first few clickable elements (they tend to be nav/filter buttons)
        card_idx = min(best_idx, len(cards) - 1) if cards else 0
        if cards:
            cards[card_idx].click()

    time.sleep(4)

    # Scrape the menu, excluding the restaurant's own name
    return _scrape_menu(driver, exclude={chosen})


def _scrape_menu(
    driver: webdriver.Remote, exclude: set[str] | None = None,
) -> list[dict]:
    """Read menu items from the current restaurant screen.

    Scrolls down to load more items and filters out header noise
    (addresses, disclaimers, navigation elements).
    """
    menu = []
    seen = set(exclude or set())

    # Scroll down a few times to load menu items past the header
    screen_size = driver.get_window_size()
    start_y = int(screen_size["height"] * 0.75)
    end_y = int(screen_size["height"] * 0.25)
    center_x = int(screen_size["width"] * 0.5)

    for scroll in range(6):
        items = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
        for item in items:
            text = item.text.strip()
            if (
                text
                and len(text) > 2
                and len(text) < 100  # Skip long disclaimers
                and text not in _MENU_NOISE
                and text not in _SEARCH_NOISE
                and text not in seen
                and not text.startswith("$")
                and "min" not in text.lower().split()
                and "order" not in text.lower().split()
                and "open now" not in text.lower()
                and "pricing" not in text.lower()
                and "Search" not in text
                and "line size" not in text.lower()
                and "no line" not in text.lower()
                and "skip the line" not in text.lower()
                and "free delivery" not in text.lower()
                and "Restaurants, dishes" not in text
                and "All Restaurants" not in text
                and "W." not in text[:10]  # Skip addresses
                and "Ave" not in text
                and "fee" not in text.lower()
            ):
                seen.add(text)
                menu.append({"name": text})

        # Swipe up to reveal more
        driver.swipe(center_x, start_y, center_x, end_y, duration=600)
        time.sleep(1.5)

    return menu[:40]


def get_menu(driver: webdriver.Remote, restaurant_index: int = 0) -> list[dict]:
    """Open a restaurant by index and get menu items.

    Prefer select_restaurant() for intelligent matching.
    This is the legacy fallback that taps by position.
    """
    wait = WebDriverWait(driver, 15)
    cards = driver.find_elements(AppiumBy.CLASS_NAME, "android.view.ViewGroup")
    if restaurant_index < len(cards):
        cards[restaurant_index].click()
    time.sleep(3)
    return _scrape_menu(driver)


def _handle_required_choices(driver: webdriver.Remote) -> None:
    """Select default options for all required customization choices.

    Grubhub items often require the user to choose a size, sleeve, milk, etc.
    before the "Add to bag" button becomes available.  This function scrolls
    through each required section and picks sensible defaults (the cheapest
    option or the "no-frills" variant).
    """
    # Preferred defaults — matched case-insensitively against option text.
    # Order matters: first match wins within each required section.
    _PREFERRED = [
        "small", "regular", "no sleeve", "paper sleeve",
        "2% milk", "no whipped", "none", "no ",
    ]

    screen = driver.get_window_size()
    cx = screen["width"] // 2
    start_y = int(screen["height"] * 0.70)
    end_y = int(screen["height"] * 0.30)

    max_scrolls = 6
    selected_sections: set[str] = set()

    for _ in range(max_scrolls):
        # Check if the button already says "Add to bag" (all choices made)
        btns = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
        for btn in btns:
            if btn.text and ("Add to" in btn.text or "add to" in btn.text):
                logger.info("All required choices made — button ready: '%s'", btn.text)
                return

        # Find all text elements to locate required sections and their options
        elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
        texts_and_els = [(el.text.strip(), el) for el in elements if el.text and el.text.strip()]

        in_required_section = False
        section_name = ""
        section_options: list[tuple[str, object]] = []

        for text, el in texts_and_els:
            if "Choose one (Required)" in text:
                # Flush previous section if we had one
                if section_options and section_name not in selected_sections:
                    _pick_best_option(section_options, _PREFERRED, section_name, selected_sections)
                in_required_section = True
                section_options = []
                continue

            if in_required_section:
                # Skip price modifiers, headers, etc.
                if text.startswith("+") or text.startswith("$"):
                    continue
                if "Choose" in text or "Required" in text or "Optional" in text:
                    # New section or end of required section
                    if section_options and section_name not in selected_sections:
                        _pick_best_option(section_options, _PREFERRED, section_name, selected_sections)
                    if "Optional" in text:
                        in_required_section = False
                    section_options = []
                    continue
                # This looks like a selectable option
                section_name = text
                section_options.append((text, el))

        # Flush last section
        if section_options and section_name not in selected_sections:
            _pick_best_option(section_options, _PREFERRED, section_name, selected_sections)

        # Scroll to find more required sections
        driver.swipe(cx, start_y, cx, end_y, duration=500)
        time.sleep(1.5)


def _pick_best_option(
    options: list[tuple[str, object]],
    preferred: list[str],
    section_name: str,
    selected_sections: set[str],
) -> None:
    """Tap the best option from a required section, preferring defaults."""
    # Try preferred keywords first
    for pref in preferred:
        for text, el in options:
            if pref in text.lower():
                logger.info("Required choice: selected '%s' (preferred match '%s')", text, pref)
                el.click()
                selected_sections.add(section_name)
                time.sleep(0.5)
                return
    # Fall back to first option
    if options:
        text, el = options[0]
        logger.info("Required choice: selected '%s' (first available)", text)
        el.click()
        selected_sections.add(section_name)
        time.sleep(0.5)


def find_and_add_to_cart(
    driver: webdriver.Remote, item_name: str, menu_items: list[dict]
) -> bool:
    """Intelligently find a menu item and add it to cart.

    Uses the LLM to match the user's request to actual menu items,
    handles required customization choices, then adds to bag.
    """
    from backend.integrations.grubhub.intelligence import pick_menu_item

    # Ask the intelligence layer which menu item matches
    matched_name = pick_menu_item(item_name, menu_items)
    if matched_name is None:
        logger.warning("No menu match found for '%s'", item_name)
        return False

    logger.info("Menu match: '%s' → '%s'", item_name, matched_name)

    wait = WebDriverWait(driver, 10)
    try:
        # Scroll to find the matched item — it may be off-screen after menu scraping
        screen = driver.get_window_size()
        cx = screen["width"] // 2
        # First scroll back to the top
        for _ in range(6):
            driver.swipe(cx, int(screen["height"] * 0.25), cx, int(screen["height"] * 0.75), duration=400)
        time.sleep(1)

        item_el = None
        for _ in range(8):
            try:
                item_el = driver.find_element(
                    AppiumBy.XPATH, f'//*[contains(@text, "{matched_name}")]'
                )
                break
            except Exception:
                # Swipe down to look for it
                driver.swipe(cx, int(screen["height"] * 0.70), cx, int(screen["height"] * 0.30), duration=500)
                time.sleep(1)

        if item_el is None:
            logger.warning("Could not find '%s' on screen after scrolling", matched_name)
            return False

        item_el.click()
        time.sleep(2)

        # Check if there are required choices to make first
        btns = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
        has_required = any(
            b.text and "required choices" in b.text.lower() for b in btns
        )
        if has_required:
            logger.info("Item has required choices — selecting defaults")
            _handle_required_choices(driver)

        # Now look for "Add to bag" / "Add to order" button
        add_btn = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH,
                 "//*[contains(@text, 'Add to') or contains(@text, 'add to')]")
            )
        )
        add_btn.click()
        time.sleep(1)
        return True

    except Exception:
        logger.exception("Failed to add '%s' (matched as '%s') to cart", item_name, matched_name)
        return False


def add_to_cart(driver: webdriver.Remote, item_name: str) -> bool:
    """Add a menu item to cart by name (legacy — no LLM matching).

    Prefer find_and_add_to_cart() for intelligent matching.
    """
    wait = WebDriverWait(driver, 10)
    try:
        item = driver.find_element(AppiumBy.XPATH, f"//*[contains(@text, '{item_name}')]")
        item.click()
        time.sleep(2)

        add_btn = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, "//*[contains(@text, 'Add to') or contains(@text, 'add to')]")
            )
        )
        add_btn.click()
        return True
    except Exception:
        logger.exception("Failed to add %s to cart", item_name)
        return False


def _tap_text(driver: webdriver.Remote, *candidates: str, timeout: int = 15) -> bool:
    """Find and tap an element matching any of the candidate text fragments."""
    xpath_parts = " or ".join(f"contains(@text, '{c}')" for c in candidates)
    xpath = f"//*[{xpath_parts}]"
    wait = WebDriverWait(driver, timeout)
    try:
        el = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, xpath)))
        # If not clickable, try parent
        if el.get_attribute("clickable") != "true":
            try:
                el.find_element(AppiumBy.XPATH, "./..").click()
            except Exception:
                el.click()
        else:
            el.click()
        return True
    except Exception:
        return False


def checkout(driver: webdriver.Remote, dry_run: bool = True) -> str:
    """Proceed to checkout. Returns order status message.

    Grubhub's checkout is multi-step:
      1. Tap "View order" / "View bag" to open the cart panel
      2. Tap "Proceed to checkout" to go to the checkout screen
      3. Tap "Place order" / "Submit" to finalize (skipped if dry_run=True)

    Args:
        dry_run: If True (default), stop before placing the order. The cart
                 contents are verified but nothing is actually purchased.
    """
    try:
        # Step 1: Open the cart
        if not _tap_text(driver, "View order", "View bag", "Cart"):
            return "Checkout failed — could not find the cart button."
        time.sleep(3)

        # Step 2: Proceed to checkout
        if not _tap_text(driver, "Proceed to checkout"):
            logger.info("No 'Proceed to checkout' — trying Place order directly")
        else:
            time.sleep(3)

        if dry_run:
            logger.info("Dry run — stopping before placing order")
            return "Order ready to place (dry run — not submitted)."

        # Step 3: Place the order
        if not _tap_text(driver, "Place order", "Submit order", "Submit"):
            return "Checkout failed — could not find the Place Order button."
        time.sleep(3)

        return "Order placed successfully!"
    except Exception:
        logger.exception("Checkout failed")
        return "Checkout failed — please complete the order manually in the app."


# ── High-level intelligent order flow ──────────────────────────────────


def intelligent_order(
    driver: webdriver.Remote,
    restaurant_name: str,
    items: str,
) -> dict:
    """Full ordering flow with LLM intelligence between every step.

    Args:
        driver: Appium driver connected to Grubhub.
        restaurant_name: The restaurant the user wants to order from.
        items: Comma-separated item names the user wants.

    Returns:
        dict with keys: added (list), failed (list), checkout_result (str)
    """
    # Step 1: Search for the restaurant
    logger.info("Intelligent order: searching for '%s'", restaurant_name)
    results = search_restaurants(driver, restaurant_name)
    if not results:
        return {
            "added": [],
            "failed": items.split(","),
            "checkout_result": f"No restaurants found for '{restaurant_name}'.",
        }

    # Step 2: LLM picks the right restaurant and opens its menu
    menu = select_restaurant(driver, restaurant_name, results)
    if not menu:
        return {
            "added": [],
            "failed": items.split(","),
            "checkout_result": "Could not load the restaurant menu.",
        }
    logger.info("Menu loaded with %d items", len(menu))

    # Step 3: For each requested item, LLM matches to actual menu items
    item_list = [i.strip() for i in items.split(",")]
    added, failed = [], []
    for item_name in item_list:
        if find_and_add_to_cart(driver, item_name, menu):
            added.append(item_name)
        else:
            failed.append(item_name)

    # Step 4: Checkout
    if added:
        result = checkout(driver)
    else:
        result = "Nothing was added to cart — skipping checkout."

    return {"added": added, "failed": failed, "checkout_result": result}
