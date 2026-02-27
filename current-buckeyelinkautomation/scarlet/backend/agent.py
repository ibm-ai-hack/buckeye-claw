import asyncio
import json
import logging
import os

from dotenv import load_dotenv

from browser_use import Agent, Browser
from browser_use.browser.profile import BrowserProfile
from browser_use.llm import ChatBrowserUse

load_dotenv()

logger = logging.getLogger(__name__)

VIEWPORT_W = 1280
VIEWPORT_H = 800

TASK_PROMPT = """You are on an authenticated BuckeyeLink (PeopleSoft) session at Ohio State University. \
Your goal is to navigate to the student's class schedule for the current term. Steps:

1. Look for 'Student Center' link or tile and click it
2. In the Student Center, find 'My Class Schedule' or 'Weekly Schedule' or look under the 'Academics' section
3. If you see a term selection, pick the most recent/current term (Spring 2026)
4. Once you can see the schedule, extract EVERY class with: course code (e.g. CSE 2421), \
course title (e.g. Systems I: Introduction to Low-Level Programming), days of week (e.g. Mon Wed Fri), \
start time, end time, building and room number, and instructor name
5. Make sure you scroll down to see ALL classes, don't stop at just the first few visible ones
6. Return all the data you found"""

AUTH_DOMAINS = ("login.osu.edu", "webauth.service.ohio-state.edu", "shibboleth")
DASHBOARD_MARKERS = ("buckeyelink.osu.edu/psp", "buckeyelink.osu.edu/psc")


class BuckeyeLinkAgent:
    def __init__(self):
        self.browser: Browser | None = None
        self.status: str = "idle"
        # idle | awaiting_auth | authenticated | extracting | complete | error
        self.schedule: dict | None = None
        self.error_message: str | None = None
        self._saw_sso = False  # True once we've seen the SSO login page

    async def start(self):
        """Open a headless browser to BuckeyeLink and wait for user to authenticate."""
        logger.info("Starting headless browser session for BuckeyeLink")
        try:
            self.browser = Browser(
                headless=True,
                browser_profile=BrowserProfile(
                    viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
                    window_size={"width": VIEWPORT_W, "height": VIEWPORT_H},
                    keep_alive=True,
                ),
            )
            await self.browser.start()
            logger.info("Browser started, navigating to BuckeyeLink")
            await self.browser.navigate_to("https://buckeyelink.osu.edu")
            self.status = "awaiting_auth"
            logger.info("Status set to awaiting_auth — waiting for user login")
        except Exception as e:
            logger.error("Failed to start browser: %s", e)
            self.status = "error"
            self.error_message = str(e)
            raise

    async def _get_page(self):
        """Get the current browser-use Page object."""
        if self.browser is None:
            raise RuntimeError("Browser not started")
        page = await self.browser.get_current_page()
        if page is None:
            raise RuntimeError("No active page")
        return page

    async def handle_click(self, x: float, y: float):
        """Handle a click at normalized coordinates (0-1 range).

        Converts to pixel coordinates and dispatches via CDP.
        """
        pixel_x = int(x * VIEWPORT_W)
        pixel_y = int(y * VIEWPORT_H)
        logger.info("Click at normalized (%.3f, %.3f) → pixel (%d, %d)", x, y, pixel_x, pixel_y)

        try:
            page = await self._get_page()
            mouse = await page.mouse
            await mouse.click(pixel_x, pixel_y)
            await asyncio.sleep(0.2)
        except Exception as e:
            logger.error("Click failed: %s", e)

    async def handle_keyboard(self, text: str | None = None, key: str | None = None):
        """Handle keyboard input.

        - key: special key name (Enter, Tab, Backspace, etc.) — uses page.press()
        - text: regular text to type — uses CDP Input.insertText per character
        """
        try:
            page = await self._get_page()

            if key:
                logger.info("Key press: %s", key)
                await page.press(key)
                return

            if text:
                logger.info("Typing text: %s", repr(text))
                session_id = await page._ensure_session()
                for char in text:
                    # Use CDP insertText for reliable text input into form fields
                    await page._client.send.Input.insertText(
                        {"text": char},
                        session_id=session_id,
                    )
                    await asyncio.sleep(0.05)
        except Exception as e:
            logger.error("Keyboard input failed: %s", e)

    async def poll_for_auth(self) -> bool:
        """Check if the user has completed Shibboleth login.

        Returns True once authenticated, False if still waiting.
        """
        if self.browser is None:
            logger.warning("poll_for_auth called but browser is None")
            return False

        try:
            url = await self.browser.get_current_page_url()
            logger.debug("Polling auth — current URL: %s", url)

            still_on_sso = any(domain in url.lower() for domain in AUTH_DOMAINS)
            on_dashboard = any(marker in url.lower() for marker in DASHBOARD_MARKERS)

            # Track that we've seen the SSO page at least once
            if still_on_sso:
                self._saw_sso = True

            # Only consider auth complete if we've been through SSO first
            # and now landed on the authenticated dashboard
            if self._saw_sso and (on_dashboard or (not still_on_sso and "buckeyelink.osu.edu" in url.lower())):
                logger.info("Authentication detected — URL: %s", url)
                self.status = "authenticated"
                return True

            logger.debug("Still awaiting auth (URL: %s)", url)
            return False
        except Exception as e:
            logger.error("Error polling for auth: %s", e)
            return False

    async def extract_schedule(self) -> dict:
        """Run the browser-use agent to navigate and extract the class schedule."""
        if self.browser is None:
            raise RuntimeError("Browser not started")

        self.status = "extracting"
        logger.info("Starting schedule extraction agent")

        try:
            api_key = os.getenv("BROWSER_USE_API_KEY")
            llm = ChatBrowserUse(model="bu-2-0", api_key=api_key)

            agent = Agent(
                task=TASK_PROMPT,
                llm=llm,
                browser=self.browser,
                max_actions_per_step=4,
                use_thinking=True,
            )

            result = await agent.run(max_steps=30)
            raw_text = result.final_result() or ""
            logger.info("Agent finished. Raw result length: %d", len(raw_text))
            logger.debug("Raw result: %s", raw_text[:2000])

            schedule = self._parse_schedule(raw_text)
            self.schedule = schedule
            self.status = "complete"
            logger.info("Schedule extraction complete — %d courses found", len(schedule.get("courses", [])))
            return schedule

        except Exception as e:
            logger.error("Schedule extraction failed: %s", e)
            self.status = "error"
            self.error_message = str(e)
            raise

    def _parse_schedule(self, raw_text: str) -> dict:
        """Try to parse the agent output into structured schedule JSON."""
        try:
            data = json.loads(raw_text)
            if "courses" in data:
                logger.info("Direct JSON parse succeeded")
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        if "```" in raw_text:
            for block in raw_text.split("```"):
                block = block.strip()
                if block.startswith("json"):
                    block = block[4:].strip()
                try:
                    data = json.loads(block)
                    if "courses" in data:
                        logger.info("Extracted JSON from code block")
                        return data
                except (json.JSONDecodeError, TypeError):
                    continue

        logger.warning("Could not parse structured schedule, returning raw text")
        return {
            "term": "Spring 2026",
            "courses": [],
            "raw": raw_text,
        }

    async def get_screenshot(self) -> bytes:
        """Take a screenshot of the current browser page."""
        if self.browser is None:
            raise RuntimeError("Browser not started")
        logger.debug("Taking screenshot")
        return await self.browser.take_screenshot(full_page=False)

    async def close(self):
        """Close the browser and reset all state."""
        logger.info("Closing browser session")
        if self.browser is not None:
            try:
                await self.browser.stop()
            except Exception as e:
                logger.warning("Error stopping browser: %s", e)
            self.browser = None
        self.status = "idle"
        self.schedule = None
        self.error_message = None
        logger.info("Session closed and state reset")
