"""
BuckeyeLink page navigation and data extraction helpers.

BuckeyeLink is a React SPA at buckeyelink.osu.edu.
URL patterns:
  /launch-task/all/<task>   — launches a task (may open PeopleSoft iframe)
  /task/all/<task>          — task detail page
  /collection/all/<group>   — grouped task collection

Key pages:
  /launch-task/all/my-class-schedule    — Class schedule
  /task/all/grades                       — View grades
  /task/all/financial-aid-status         — Financial aid
  /task/all/schedule-planner             — Schedule planner
  /collection/all/holds-todos            — Holds & to-do list
  /collection/all/enrollment-center      — Enrollment & registration
"""

import logging

from playwright.async_api import Page

from buckeyelink.auth import get_authenticated_context, BASE_URL

logger = logging.getLogger(__name__)

# Known BuckeyeLink routes
URLS = {
    "schedule": f"{BASE_URL}/launch-task/all/my-class-schedule",
    "grades": f"{BASE_URL}/task/all/grades",
    "financial_aid": f"{BASE_URL}/task/all/financial-aid-status",
    "schedule_planner": f"{BASE_URL}/task/all/schedule-planner",
    "holds_todos": f"{BASE_URL}/collection/all/holds-todos",
    "enrollment": f"{BASE_URL}/collection/all/enrollment-center",
    "dashboard": BASE_URL,
}


async def open_page(key_or_url: str) -> Page:
    """Open a BuckeyeLink page. Pass a key from URLS dict or a full URL."""
    context = await get_authenticated_context()
    page = await context.new_page()

    url = URLS.get(key_or_url, key_or_url)
    logger.info("Navigating to: %s", url)
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    # BuckeyeLink is a React SPA — wait for the app to render
    await _wait_for_spa_load(page)

    return page


async def _wait_for_spa_load(page: Page, timeout: int = 15000) -> None:
    """Wait for the React SPA to finish loading content."""
    try:
        # Wait for the main content area to appear
        # BuckeyeLink uses common React patterns — look for rendered content
        await page.wait_for_function(
            """() => {
                const body = document.body;
                // SPA has loaded when there's substantial content beyond the loading spinner
                const text = body.innerText || '';
                return text.length > 100 && !text.includes('Loading');
            }""",
            timeout=timeout,
        )
    except Exception:
        logger.debug("SPA load wait timed out — proceeding with current state")


async def extract_visible_text(page: Page) -> str:
    """Extract all visible text from the page."""
    return await page.evaluate("""() => {
        return document.body.innerText || document.body.textContent || '';
    }""")


async def extract_text_by_selector(page: Page, selector: str) -> str:
    """Extract text from a specific element."""
    try:
        el = await page.wait_for_selector(selector, timeout=10000)
        if el:
            return (await el.text_content() or "").strip()
    except Exception:
        logger.debug("Element not found: %s", selector)
    return ""


async def extract_all_text_by_selector(page: Page, selector: str) -> list[str]:
    """Extract text from all matching elements."""
    elements = await page.query_selector_all(selector)
    results = []
    for el in elements:
        text = (await el.text_content() or "").strip()
        if text:
            results.append(text)
    return results


async def extract_table_data(page: Page, table_selector: str = "table") -> list[dict]:
    """Extract data from an HTML table into a list of dicts."""
    rows = await page.query_selector_all(f"{table_selector} tr")
    if not rows:
        return []

    headers = []
    data = []
    for i, row in enumerate(rows):
        cells = await row.query_selector_all("th, td")
        cell_texts = [(await c.text_content() or "").strip() for c in cells]
        if i == 0 and not headers:
            headers = cell_texts
        elif cell_texts:
            if headers and len(cell_texts) == len(headers):
                data.append(dict(zip(headers, cell_texts)))
            else:
                data.append({"cells": cell_texts})
    return data


async def extract_card_data(page: Page) -> list[dict]:
    """Extract data from BuckeyeLink card-style layouts (common in the React SPA)."""
    # BuckeyeLink renders info in cards — try common card patterns
    cards = []

    # Try extracting from common card/list patterns
    card_elements = await page.query_selector_all(
        '[class*="card"], [class*="Card"], [class*="task"], [class*="item"], [role="listitem"]'
    )

    for el in card_elements:
        text = (await el.text_content() or "").strip()
        if text and len(text) > 5:
            cards.append({"content": text})

    return cards


async def get_iframe_content(page: Page) -> str | None:
    """Some BuckeyeLink tasks open PeopleSoft in an iframe. Extract its content."""
    frames = page.frames
    for frame in frames:
        if frame != page.main_frame:
            try:
                content = await frame.evaluate("() => document.body.innerText || ''")
                if content and len(content) > 50:
                    return content
            except Exception:
                continue
    return None
