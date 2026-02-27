"""
Grubhub ordering automation via Appium + Android emulator.

This module drives the Grubhub app UI to search restaurants, browse menus,
and place orders. Requires a running Android emulator with Grubhub installed
and an Appium server running locally.
"""

import logging
import time
from typing import Any

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

GRUBHUB_PACKAGE = "com.grubhub.android"
APPIUM_URL = "http://localhost:4723"


def get_driver() -> webdriver.Remote:
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.app_package = GRUBHUB_PACKAGE
    options.app_activity = f"{GRUBHUB_PACKAGE}.ui.LaunchActivity"
    options.no_reset = True
    return webdriver.Remote(APPIUM_URL, options=options)


def search_restaurants(driver: webdriver.Remote, query: str) -> list[dict]:
    """Search for restaurants in the Grubhub app."""
    wait = WebDriverWait(driver, 15)

    # Tap search
    search_btn = wait.until(
        EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, "Search"))
    )
    search_btn.click()
    time.sleep(1)

    # Type query
    search_field = wait.until(
        EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
    )
    search_field.clear()
    search_field.send_keys(query)
    time.sleep(2)

    # Collect results
    results = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    restaurants = []
    for el in results:
        text = el.text.strip()
        if text and len(text) > 2:
            restaurants.append({"name": text})
    return restaurants[:10]


def get_menu(driver: webdriver.Remote, restaurant_index: int = 0) -> list[dict]:
    """Open a restaurant and get menu items. Call search_restaurants first."""
    wait = WebDriverWait(driver, 15)

    # Tap on restaurant card
    cards = driver.find_elements(AppiumBy.CLASS_NAME, "android.view.ViewGroup")
    if restaurant_index < len(cards):
        cards[restaurant_index].click()
    time.sleep(3)

    # Scrape menu items
    items = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    menu = []
    for item in items:
        text = item.text.strip()
        if text and "$" not in text and len(text) > 2:
            menu.append({"name": text})
    return menu[:20]


def add_to_cart(driver: webdriver.Remote, item_name: str) -> bool:
    """Add a menu item to cart by name."""
    wait = WebDriverWait(driver, 10)
    try:
        item = driver.find_element(AppiumBy.XPATH, f"//*[contains(@text, '{item_name}')]")
        item.click()
        time.sleep(2)

        # Look for "Add to bag" button
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


def checkout(driver: webdriver.Remote) -> str:
    """Proceed to checkout. Returns order status message."""
    wait = WebDriverWait(driver, 15)
    try:
        # Tap cart/bag icon
        cart = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, "//*[contains(@text, 'View bag') or contains(@text, 'Cart')]")
            )
        )
        cart.click()
        time.sleep(2)

        # Tap place order
        place_order = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, "//*[contains(@text, 'Place order') or contains(@text, 'Submit')]")
            )
        )
        place_order.click()
        time.sleep(3)

        return "Order placed successfully!"
    except Exception:
        logger.exception("Checkout failed")
        return "Checkout failed — please complete the order manually in the app."
