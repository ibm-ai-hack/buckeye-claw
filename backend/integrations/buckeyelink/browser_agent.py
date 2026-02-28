"""
Browser-use wrapper for automated BuckeyeLink task execution.

Injects Playwright SSO cookies into a browser-use session and runs
an LLM-driven agent to navigate and extract data.

This module is used by the main BeeAI agent (via query_buckeyelink tool).
It does NOT replace the frontend web UI agent.
"""

import logging
import os

from browser_use import Agent, Browser
from browser_use.browser.profile import BrowserProfile
from browser_use.llm import ChatBrowserUse

from backend.integrations.buckeyelink.auth import get_authenticated_context, BASE_URL

logger = logging.getLogger(__name__)


async def run_browser_use_task(task_prompt: str, max_steps: int = 30) -> str:
    """Run a browser-use agent on BuckeyeLink with pre-authenticated cookies.

    Flow:
        1. Get Playwright session cookies via auth.get_authenticated_context()
        2. Start a browser-use Browser (headless)
        3. Inject cookies via CDP
        4. Navigate to buckeyelink.osu.edu, verify auth succeeded
        5. Create browser-use Agent with ChatBrowserUse LLM
        6. Run the agent with the task prompt
        7. Return the final result text
        8. Close browser

    Args:
        task_prompt: The enhanced prompt with NAVIGATION/EXTRACTION/FORMAT sections.
        max_steps: Maximum agent steps (default 30).

    Returns:
        The extracted text result from the browser-use agent.
    """
    browser = None
    try:
        # 1. Get authenticated Playwright context and extract cookies
        pw_context = await get_authenticated_context()
        cookies = await pw_context.cookies()
        logger.info("Got %d cookies from Playwright session", len(cookies))

        # 2. Start browser-use browser (headless)
        browser = Browser(
            headless=True,
            browser_profile=BrowserProfile(
                viewport={"width": 1280, "height": 900},
                window_size={"width": 1280, "height": 900},
            ),
        )
        await browser.start()
        logger.info("Browser-use browser started")

        # 3. Inject cookies via CDP
        page = await browser.get_current_page()

        # Convert Playwright cookies to CDP Network.setCookie format
        cdp_cookies = []
        for c in cookies:
            cdp_cookie = {
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ""),
                "path": c.get("path", "/"),
            }
            if c.get("expires", -1) > 0:
                cdp_cookie["expires"] = c["expires"]
            if c.get("secure"):
                cdp_cookie["secure"] = True
            if c.get("httpOnly"):
                cdp_cookie["httpOnly"] = True
            if c.get("sameSite"):
                cdp_cookie["sameSite"] = c["sameSite"]
            cdp_cookies.append(cdp_cookie)

        # Use CDP attribute-chain syntax (browser-use convention)
        session_id = await page._ensure_session()
        await page._client.send.Network.setCookies(
            {"cookies": cdp_cookies},
            session_id=session_id,
        )
        logger.info("Injected %d cookies via CDP", len(cdp_cookies))

        # 4. Navigate to BuckeyeLink and verify auth
        await page.goto(BASE_URL)
        current_url = await browser.get_current_page_url()
        logger.info("Navigated to BuckeyeLink, current URL: %s", current_url)

        if "webauth.service.ohio-state.edu" in current_url or "/login" in current_url:
            raise RuntimeError(
                "Cookie injection failed — redirected to login. "
                "The Playwright session may have expired."
            )

        # 5. Create browser-use agent
        api_key = os.getenv("BROWSER_USE_API_KEY")
        llm = ChatBrowserUse(model="bu-2-0", api_key=api_key)

        agent = Agent(
            task=task_prompt,
            llm=llm,
            browser=browser,
            max_actions_per_step=4,
            use_thinking=True,
        )

        # 6. Run the agent
        logger.info("Running browser-use agent (max_steps=%d)", max_steps)
        result = await agent.run(max_steps=max_steps)

        # 7. Extract final result
        final = result.final_result() or ""
        logger.info("Browser-use agent finished, result length: %d", len(final))
        return final

    except Exception:
        logger.exception("browser-use task failed")
        raise

    finally:
        # 8. Clean up
        if browser is not None:
            try:
                await browser.stop()
            except Exception as e:
                logger.warning("Error stopping browser-use browser: %s", e)
