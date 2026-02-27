"""
BuckeyeLink tools for the BeeAI agent.

BuckeyeLink (buckeyelink.osu.edu) is a React SPA that wraps PeopleSoft.
Some tasks render inline, others open PeopleSoft in an iframe.
We use Playwright to navigate the SPA and extract rendered content.
"""

import logging

from beeai_framework.tools import StringToolOutput, tool

logger = logging.getLogger(__name__)


def _truncate(text: str, limit: int = 1400) -> str:
    if len(text) > limit:
        return text[:limit] + "... (truncated)"
    return text


@tool
async def get_class_schedule() -> StringToolOutput:
    """Get the student's current class schedule from BuckeyeLink."""
    try:
        from buckeyelink.browser import open_page, extract_visible_text, extract_table_data, get_iframe_content

        page = await open_page("schedule")

        # The schedule page may render as a table in a PeopleSoft iframe
        # or as React-rendered content
        iframe_text = await get_iframe_content(page)
        if iframe_text:
            await page.close()
            return StringToolOutput(_truncate(f"Your class schedule:\n{iframe_text}"))

        # Try table extraction (PeopleSoft pattern)
        tables = await extract_table_data(page)
        if tables:
            await page.close()
            lines = []
            for row in tables:
                if "cells" in row:
                    lines.append(" | ".join(row["cells"]))
                else:
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    lines.append(" | ".join(parts))
            return StringToolOutput(_truncate("Your class schedule:\n" + "\n".join(lines)))

        # Fallback: extract all visible text from the page
        text = await extract_visible_text(page)
        await page.close()

        if text.strip():
            return StringToolOutput(_truncate(f"Your class schedule:\n{text}"))
        return StringToolOutput("Could not load class schedule. You may need to log in again.")
    except Exception as e:
        logger.exception("BuckeyeLink schedule error")
        return StringToolOutput(
            f"BuckeyeLink unavailable: {type(e).__name__}. "
            "Make sure OSU_USERNAME and OSU_PASSWORD are set in .env."
        )


@tool
async def get_grades() -> StringToolOutput:
    """Get the student's grades from BuckeyeLink."""
    try:
        from buckeyelink.browser import open_page, extract_visible_text, extract_table_data, get_iframe_content

        page = await open_page("grades")

        iframe_text = await get_iframe_content(page)
        if iframe_text:
            await page.close()
            return StringToolOutput(_truncate(f"Your grades:\n{iframe_text}"))

        tables = await extract_table_data(page)
        if tables:
            await page.close()
            lines = []
            for row in tables:
                if "cells" in row:
                    lines.append(" | ".join(row["cells"]))
                else:
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    lines.append(" | ".join(parts))
            return StringToolOutput(_truncate("Your grades:\n" + "\n".join(lines)))

        text = await extract_visible_text(page)
        await page.close()

        if text.strip():
            return StringToolOutput(_truncate(f"Your grades:\n{text}"))
        return StringToolOutput("Could not load grades. You may need to log in again.")
    except Exception as e:
        logger.exception("BuckeyeLink grades error")
        return StringToolOutput(f"BuckeyeLink unavailable: {type(e).__name__}.")


@tool
async def get_financial_aid_status() -> StringToolOutput:
    """Check financial aid status on BuckeyeLink."""
    try:
        from buckeyelink.browser import open_page, extract_visible_text, get_iframe_content

        page = await open_page("financial_aid")

        iframe_text = await get_iframe_content(page)
        if iframe_text:
            await page.close()
            return StringToolOutput(_truncate(f"Financial aid status:\n{iframe_text}"))

        text = await extract_visible_text(page)
        await page.close()

        if text.strip():
            return StringToolOutput(_truncate(f"Financial aid status:\n{text}"))
        return StringToolOutput("Could not load financial aid info. Check BuckeyeLink directly.")
    except Exception as e:
        logger.exception("BuckeyeLink financial aid error")
        return StringToolOutput(f"BuckeyeLink unavailable: {type(e).__name__}.")


@tool
async def get_holds_and_todos() -> StringToolOutput:
    """Check for account holds and to-do items on BuckeyeLink."""
    try:
        from buckeyelink.browser import open_page, extract_visible_text, extract_card_data

        page = await open_page("holds_todos")

        cards = await extract_card_data(page)
        if cards:
            await page.close()
            lines = [c["content"] for c in cards]
            return StringToolOutput(_truncate("Holds & To-Do Items:\n" + "\n---\n".join(lines)))

        text = await extract_visible_text(page)
        await page.close()

        if text.strip():
            return StringToolOutput(_truncate(f"Holds & To-Do Items:\n{text}"))
        return StringToolOutput("No holds or to-do items found, or page could not be loaded.")
    except Exception as e:
        logger.exception("BuckeyeLink holds/todos error")
        return StringToolOutput(f"BuckeyeLink unavailable: {type(e).__name__}.")


@tool
async def get_enrollment_info() -> StringToolOutput:
    """Get enrollment and registration information from BuckeyeLink."""
    try:
        from buckeyelink.browser import open_page, extract_visible_text, extract_card_data

        page = await open_page("enrollment")

        cards = await extract_card_data(page)
        if cards:
            await page.close()
            lines = [c["content"] for c in cards]
            return StringToolOutput(_truncate("Enrollment Info:\n" + "\n---\n".join(lines)))

        text = await extract_visible_text(page)
        await page.close()

        if text.strip():
            return StringToolOutput(_truncate(f"Enrollment Info:\n{text}"))
        return StringToolOutput("Could not load enrollment info.")
    except Exception as e:
        logger.exception("BuckeyeLink enrollment error")
        return StringToolOutput(f"BuckeyeLink unavailable: {type(e).__name__}.")


@tool
async def get_buckeyelink_dashboard() -> StringToolOutput:
    """Get the BuckeyeLink dashboard overview — shows academics, finances, announcements."""
    try:
        from buckeyelink.browser import open_page, extract_visible_text

        page = await open_page("dashboard")
        text = await extract_visible_text(page)
        await page.close()

        if text.strip():
            return StringToolOutput(_truncate(f"BuckeyeLink Dashboard:\n{text}"))
        return StringToolOutput("Could not load BuckeyeLink dashboard.")
    except Exception as e:
        logger.exception("BuckeyeLink dashboard error")
        return StringToolOutput(f"BuckeyeLink unavailable: {type(e).__name__}.")
