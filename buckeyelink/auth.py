"""
auth.py — Deterministic login flow with Duo MFA pause.

This is 100% browser_use CDP (no AI agent). The login flow at OSU is:
  1. buckeyelink.osu.edu → redirects to login.osu.edu (Shibboleth/CAS)
  2. Enter username + password
  3. Duo MFA prompt → user approves push on phone
  4. Handle post-MFA screens (trust browser, remember device, etc.)
  5. Redirect back to BuckeyeLink (authenticated)
  6. Navigate to the Student Hub and wait for it to load

The script handles steps 1-2 automatically, pauses for step 3,
auto-handles step 4, and detects when step 5-6 completes.
"""

import asyncio
from config import OSU_USERNAME, OSU_PASSWORD, DUO_TIMEOUT, BUCKEYELINK_URL, STUDENT_CENTER_URL


# ─── JS Helpers (all arrow-function format for CDP) ───────────────

_JS_CLICK_SIGNIN = """() => {
    const links = document.querySelectorAll('a, button');
    for (const el of links) {
        const text = (el.textContent || '').toLowerCase().trim();
        if (text.includes('sign in') || text.includes('log in') || text.includes('login')) {
            el.click();
            return 'clicked_signin';
        }
    }
    return 'no_signin_found';
}"""

_JS_HANDLE_TRUST_BROWSER = """() => {
    // Duo's "Is this your device?" / "Trust this browser?" screen
    // Try the main page first, then check iframes
    function tryClickTrust(doc) {
        const buttons = doc.querySelectorAll('button, a, input[type="button"], input[type="submit"]');
        for (const btn of buttons) {
            const text = (btn.textContent || btn.value || '').toLowerCase().trim();
            if (text.includes('yes, trust') || text.includes('trust browser') ||
                text.includes('yes, this is my device') || text.includes('remember me')) {
                btn.click();
                return 'clicked_trust';
            }
        }
        // Also look for "Don't trust" / "No" / "Skip" as fallback
        for (const btn of buttons) {
            const text = (btn.textContent || btn.value || '').toLowerCase().trim();
            if (text.includes("don't trust") || text.includes('no, other') ||
                text.includes('skip') || text.includes('not now')) {
                btn.click();
                return 'clicked_skip';
            }
        }
        // Check for checkboxes like "Remember me for 30 days"
        const checkboxes = doc.querySelectorAll('input[type="checkbox"]');
        for (const cb of checkboxes) {
            const label = cb.closest('label') || doc.querySelector('label[for="' + cb.id + '"]');
            if (label) {
                const text = label.textContent.toLowerCase();
                if (text.includes('remember') || text.includes('trust') || text.includes('30 day')) {
                    if (!cb.checked) cb.click();
                    return 'checked_remember';
                }
            }
        }
        return null;
    }

    // Try the main document
    let result = tryClickTrust(document);
    if (result) return result;

    // Try iframes (Duo often runs inside an iframe)
    try {
        const iframes = document.querySelectorAll('iframe');
        for (const iframe of iframes) {
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                result = tryClickTrust(iframeDoc);
                if (result) return result;
            } catch (e) {
                // Cross-origin iframe, skip
            }
        }
    } catch (e) {}

    return 'no_trust_prompt';
}"""

_JS_DETECT_PAGE_STATE = """() => {
    const url = window.location.href;
    const body = document.body ? document.body.innerText.toLowerCase() : '';

    if (body.includes('trust this browser') || body.includes('is this your device') ||
        body.includes('remember this device') || body.includes('remember me')) {
        return 'trust_prompt';
    }
    if (body.includes('stay signed in') || body.includes('keep me signed in')) {
        return 'stay_signed_in';
    }
    if (body.includes('error') && (body.includes('authentication') || body.includes('login'))) {
        return 'auth_error';
    }
    if (url.includes('buckeyelink') || url.includes('student-hub')) {
        return 'buckeyelink';
    }
    if (url.includes('login.osu.edu') || url.includes('idp/')) {
        return 'login_page';
    }
    return 'unknown';
}"""

_JS_CLICK_STAY_SIGNED_IN = """() => {
    const buttons = document.querySelectorAll('button, a, input[type="button"], input[type="submit"]');
    for (const btn of buttons) {
        const text = (btn.textContent || btn.value || '').toLowerCase().trim();
        if (text.includes('yes') || text.includes('stay signed in') ||
            text.includes('keep me signed in') || text.includes('continue')) {
            btn.click();
            return 'clicked_stay';
        }
    }
    return 'no_stay_button';
}"""


def _js_fill(selector: str, value: str) -> str:
    """Generate arrow-function JS to fill a form field."""
    escaped_value = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"""() => {{
        const el = document.querySelector('{selector}');
        if (el) {{
            el.focus();
            el.value = '{escaped_value}';
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return 'filled';
        }}
        return 'not_found';
    }}"""


def _js_click(selector: str) -> str:
    """Generate arrow-function JS to click a button."""
    return f"""() => {{
        const el = document.querySelector('{selector}');
        if (el) {{
            el.click();
            return 'clicked';
        }}
        return 'not_found';
    }}"""


async def login(page) -> bool:
    """
    Log into BuckeyeLink. Returns True if login succeeds.

    The browser must NOT be headless for Duo push approval — you need
    to see the Duo prompt (or at minimum, get the push notification).
    """

    print("🔐 Starting login flow...")

    # ── Step 1: Navigate to BuckeyeLink and trigger SSO login ────
    await page.goto(BUCKEYELINK_URL)
    await asyncio.sleep(3)

    # Try clicking a "Sign In" link/button if one exists on the page
    try:
        await page.evaluate(_JS_CLICK_SIGNIN)
    except Exception:
        pass

    # Wait for SSO redirect to the login page
    redirected = False
    for _ in range(20):
        await asyncio.sleep(2)
        current_url = await page.get_url()
        if any(p in current_url for p in ["login.osu.edu", "idp/", "webauth", "shibboleth"]):
            print(f"   SSO redirect detected: {current_url}")
            redirected = True
            break

    if not redirected:
        # If no redirect, try navigating to the student hub directly
        current_url = await page.get_url()
        if "login" not in current_url and "idp" not in current_url:
            print("   Trying student hub URL to trigger auth...")
            await page.goto(STUDENT_CENTER_URL)
            for _ in range(10):
                await asyncio.sleep(2)
                current_url = await page.get_url()
                if any(p in current_url for p in ["login.osu.edu", "idp/", "webauth"]):
                    print(f"   SSO redirect detected: {current_url}")
                    redirected = True
                    break

    # Give the login form time to fully render
    await asyncio.sleep(3)

    # ── Step 2: Fill credentials ───────────────────────────────────
    username_selectors = [
        'input[name="username"]',
        'input[id="username"]',
        'input[name="j_username"]',
        '#username',
    ]

    password_selectors = [
        'input[name="password"]',
        'input[id="password"]',
        'input[name="j_password"]',
        '#password',
    ]

    # Try each selector until one works
    username_filled = await _try_fill(page, username_selectors, OSU_USERNAME)
    password_filled = await _try_fill(page, password_selectors, OSU_PASSWORD)

    if not username_filled or not password_filled:
        current_url = await page.get_url()
        print("❌ Could not find login form fields.")
        print("   The page URL is:", current_url)
        print("   You may need to update the selectors in auth.py")
        return False

    print(f"✅ Credentials entered for {OSU_USERNAME}")

    # Click the login/submit button
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button[name="submit"]',
    ]

    submitted = await _try_click(page, submit_selectors)

    if not submitted:
        # Try pressing Enter as fallback
        await page.press("Enter")
        print("✅ Login form submitted (via Enter key)")
    else:
        print("✅ Login form submitted")

    # ── Step 3: Duo MFA ────────────────────────────────────────────
    print()
    print("=" * 55)
    print("📱 DUO MFA: Approve the push notification on your phone")
    print(f"   Waiting up to {DUO_TIMEOUT} seconds...")
    print("=" * 55)
    print()

    # Wait for Duo to complete and handle post-MFA screens
    authenticated = await _wait_for_mfa_completion(page)

    if not authenticated:
        current_url = await page.get_url()
        print("❌ MFA timed out or failed.")
        print(f"   Current URL: {current_url}")
        return False

    # ── Step 4: Handle post-MFA intermediate screens ──────────────
    await _handle_post_mfa_screens(page)

    # ── Step 5: Verify we're on BuckeyeLink ───────────────────────
    current_url = await page.get_url()
    print("✅ Duo MFA approved — logged in successfully!")
    print(f"   Current URL: {current_url}")

    # ── Step 6: Navigate to Student Hub ───────────────────────────
    await navigate_to_student_hub(page)

    return True


async def _try_fill(page, selectors: list[str], value: str) -> bool:
    """Try multiple CSS selectors to fill a form field."""
    for selector in selectors:
        try:
            result = await page.evaluate(_js_fill(selector, value))
            if "filled" in str(result):
                return True
        except Exception:
            continue
    return False


async def _try_click(page, selectors: list[str]) -> bool:
    """Try multiple CSS selectors to click a button."""
    for selector in selectors:
        try:
            result = await page.evaluate(_js_click(selector))
            if "clicked" in str(result):
                return True
        except Exception:
            continue
    return False


async def _wait_for_mfa_completion(page) -> bool:
    """
    Poll the page URL to detect when Duo MFA completes.

    After the user approves the Duo push, the browser redirects
    from the login/Duo page back to BuckeyeLink. We detect this
    by checking if the URL no longer contains login-related patterns.

    Also handles the Duo "Trust this browser?" screen automatically
    if it appears before the redirect.
    """
    login_patterns = ["login.osu.edu", "webauth", "idp/", "duosecurity", "duo.com"]

    poll_interval = 2  # seconds
    elapsed = 0

    while elapsed < DUO_TIMEOUT:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        current_url = await page.get_url()

        # Check if we've left the login/Duo pages
        is_still_login = any(pattern in current_url for pattern in login_patterns)

        if not is_still_login:
            # Give the page a moment to fully load
            await asyncio.sleep(2)
            return True

        # While still on login/Duo domain, try to handle trust-browser prompts
        # (Duo sometimes shows this before redirecting away)
        try:
            state = await page.evaluate(_JS_DETECT_PAGE_STATE)
            if state == "trust_prompt":
                print("   🔒 Detected 'Trust this browser' prompt — handling...")
                result = await page.evaluate(_JS_HANDLE_TRUST_BROWSER)
                print(f"   → {result}")
                await asyncio.sleep(3)
            elif state == "stay_signed_in":
                print("   🔒 Detected 'Stay signed in' prompt — handling...")
                result = await page.evaluate(_JS_CLICK_STAY_SIGNED_IN)
                print(f"   → {result}")
                await asyncio.sleep(3)
        except Exception:
            pass

        # Print a dot every 10 seconds so user knows we're waiting
        if elapsed % 10 == 0:
            print(f"   ⏳ Still waiting... ({elapsed}s / {DUO_TIMEOUT}s)")

    return False


async def _handle_post_mfa_screens(page):
    """
    Handle intermediate screens that may appear after MFA approval
    but before fully landing on BuckeyeLink.

    Common screens:
    - Duo "Trust this browser?" / "Is this your device?"
    - Microsoft/SSO "Stay signed in?"
    - Any additional consent or confirmation pages
    """
    # Give the page a moment to settle
    await asyncio.sleep(2)

    for attempt in range(5):
        try:
            state = await page.evaluate(_JS_DETECT_PAGE_STATE)
        except Exception:
            await asyncio.sleep(2)
            continue

        if state == "buckeyelink":
            # We're where we need to be
            return

        if state == "trust_prompt":
            print("   🔒 Post-MFA: Handling 'Trust this browser' prompt...")
            try:
                result = await page.evaluate(_JS_HANDLE_TRUST_BROWSER)
                print(f"   → {result}")
            except Exception:
                pass
            await asyncio.sleep(3)

        elif state == "stay_signed_in":
            print("   🔒 Post-MFA: Handling 'Stay signed in' prompt...")
            try:
                result = await page.evaluate(_JS_CLICK_STAY_SIGNED_IN)
                print(f"   → {result}")
            except Exception:
                pass
            await asyncio.sleep(3)

        elif state == "auth_error":
            print("   ⚠️  Post-MFA: Authentication error detected on page.")
            return

        else:
            # Unknown state — wait a bit and try again
            await asyncio.sleep(2)

    # Final wait for any remaining redirects
    await asyncio.sleep(2)


async def navigate_to_student_hub(page):
    """
    After authentication, navigate to the Student Hub.
    This is the central page from which all workflows start.
    """
    current_url = await page.get_url()

    # If we're already on the student hub, great
    if "student-hub" in current_url:
        print("📍 Already on Student Hub")
        return

    print("📍 Navigating to Student Hub...")
    await page.goto(STUDENT_CENTER_URL)
    await asyncio.sleep(3)

    # Wait for the page to fully load (check for dynamic content)
    for _ in range(10):
        current_url = await page.get_url()
        if "student-hub" in current_url or "buckeyelink" in current_url:
            # Check if the page has meaningful content loaded
            try:
                has_content = await page.evaluate("""() => {
                    const body = document.body ? document.body.innerText : '';
                    return body.length > 200 ? 'loaded' : 'loading';
                }""")
                if has_content == "loaded":
                    break
            except Exception:
                pass
        await asyncio.sleep(2)

    current_url = await page.get_url()
    print(f"📍 Student Hub loaded: {current_url}")


async def ensure_authenticated(page) -> bool:
    """
    Check if already authenticated, login if not.
    Useful for resuming sessions.
    """
    await page.goto(BUCKEYELINK_URL)
    await asyncio.sleep(2)

    current_url = await page.get_url()
    # If we're on the BuckeyeLink page (not redirected to login), we're good
    if "login.osu.edu" not in current_url and "idp/" not in current_url:
        print("✅ Already authenticated")
        return True

    return await login(page)
