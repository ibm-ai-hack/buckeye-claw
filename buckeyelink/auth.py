"""
OSU Shibboleth SSO authentication via Playwright.
Handles login to buckeyelink.osu.edu through the OSU IdP.

BuckeyeLink is a React SPA. Authentication goes through:
  1. buckeyelink.osu.edu/login → redirects to Shibboleth IdP
  2. webauth.service.ohio-state.edu → username/password
  3. Duo MFA push (if enrolled)
  4. Redirect back to buckeyelink.osu.edu with session
"""

import logging
import os

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = logging.getLogger(__name__)

_context: BrowserContext | None = None
_browser: Browser | None = None
_playwright = None

BASE_URL = "https://buckeyelink.osu.edu"
LOGIN_URL = f"{BASE_URL}/login"
IDP_HOST = "webauth.service.ohio-state.edu"


async def get_authenticated_context() -> BrowserContext:
    """Get or create an authenticated browser context for BuckeyeLink."""
    global _context, _browser, _playwright

    if _context is not None:
        # Verify session is still alive by checking a quick page load
        try:
            page = await _context.new_page()
            resp = await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
            url = page.url
            await page.close()
            # If we're not redirected to login, session is good
            if IDP_HOST not in url and "/login" not in url:
                return _context
        except Exception:
            pass
        # Session expired — close and re-auth
        await close_browser()

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True)
    _context = await _browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

    page = await _context.new_page()
    await _login(page)
    await page.close()

    return _context


async def _login(page: Page) -> None:
    """Perform OSU Shibboleth SSO login."""
    username = os.environ.get("OSU_USERNAME", "")
    password = os.environ.get("OSU_PASSWORD", "")

    if not username or not password:
        raise RuntimeError("OSU_USERNAME and OSU_PASSWORD must be set in .env")

    logger.info("Navigating to BuckeyeLink login...")
    await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)

    # The login page redirects through Shibboleth
    # Wait for the IdP login form to appear
    try:
        await page.wait_for_url(f"*{IDP_HOST}*", timeout=15000)
    except Exception:
        # Might already be on the login form or a different SSO page
        logger.info("Current URL after login redirect: %s", page.url)

    # Fill Shibboleth credentials
    # OSU uses standard Shibboleth with username/password fields
    username_sel = 'input[name="username"], input[name="j_username"], #username'
    password_sel = 'input[name="password"], input[name="j_password"], #password'
    submit_sel = 'button[type="submit"], input[type="submit"], .btn-submit'

    await page.fill(username_sel, username)
    await page.fill(password_sel, password)
    await page.click(submit_sel)

    # Wait for either:
    # 1. Duo MFA prompt (iframe or push page)
    # 2. Direct redirect back to BuckeyeLink (no MFA)
    try:
        await page.wait_for_url(
            f"*buckeyelink*",
            timeout=60000,  # 60s — allows time for Duo push approval
        )
        logger.info("BuckeyeLink login successful")
    except Exception:
        current_url = page.url
        if "duo" in current_url.lower() or "mfa" in current_url.lower():
            logger.warning(
                "Waiting for Duo MFA approval. Current URL: %s. "
                "Approve the push notification on your phone.",
                current_url,
            )
            # Give extra time for MFA
            try:
                await page.wait_for_url("*buckeyelink*", timeout=120000)
                logger.info("MFA approved — BuckeyeLink login successful")
            except Exception:
                logger.error("MFA timed out after 120s. URL: %s", page.url)
                raise RuntimeError(
                    "BuckeyeLink login failed — MFA timed out. "
                    "Approve the Duo push or set up a bypass."
                )
        else:
            logger.error("Login failed. Unexpected URL: %s", current_url)
            raise RuntimeError(f"BuckeyeLink login failed. Stuck at: {current_url}")


async def close_browser() -> None:
    """Shut down the browser and clean up resources."""
    global _context, _browser, _playwright
    if _context:
        await _context.close()
        _context = None
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
