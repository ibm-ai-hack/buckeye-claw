"""
check_holds.py — Standalone script to check BuckeyeLink holds.

Usage:
    python -m backend.integrations.buckeyelink.check_holds

Logs in via Duo MFA, navigates to holds, and prints a summary.
"""

import asyncio

from browser_use import Agent, BrowserSession, Controller, ActionResult

from backend.integrations.buckeyelink.config import HEADLESS, get_llm
from backend.integrations.buckeyelink.auth import login


# ─── Controller with a single action to capture the result ────────

controller = Controller()


@controller.action("Return the exact text shown in the holds section")
async def return_holds_text(text: str) -> ActionResult:
    """Called by the agent to hand back the raw holds text from the page."""
    return ActionResult(extracted_content=text, is_done=True)


# ─── Hardcoded task prompt ────────────────────────────────────────

TASK_PROMPT = """You are on an authenticated BuckeyeLink (PeopleSoft) session at Ohio State University. \
Your goal is to find and return the student's holds (service indicators). Steps:

1. Look for 'Student Center' link or tile and click it
2. In the Student Center, find 'Holds' in the right-hand column — it may say \
'Holds', 'Service Indicators', '0 Holds', '2 Holds', or have a 'details' link next to it
3. Click on the holds link or 'details' to see the full holds information
4. Read ALL the text visible in the holds section exactly as it appears on screen — \
this could be 'No Holds', a list of hold names, hold types, what they block, \
which department placed them, dates, and resolution instructions
5. Make sure you scroll down to see ALL holds, don't stop at just the first one
6. Return all the text you found verbatim — do not summarize or reformat it"""

AUTH_DOMAINS = ("login.osu.edu", "webauth.service.ohio-state.edu", "shibboleth")
DASHBOARD_MARKERS = ("buckeyelink.osu.edu/psp", "buckeyelink.osu.edu/psc")


# ─── Main ─────────────────────────────────────────────────────────

async def main():
    print("=" * 55)
    print("  BuckeyeLink — Check Holds")
    print("=" * 55)

    browser = BrowserSession(
        headless=HEADLESS,
        disable_security=False,
        window_size={"width": 1280, "height": 900},
    )

    try:
        await browser.start()
        page = await browser.get_current_page()

        # Authenticate (fills creds, waits for Duo push)
        logged_in = await login(page)
        if not logged_in:
            print("Login failed.")
            return

        # Run the browser-use agent with the hardcoded prompt
        llm = get_llm()
        agent = Agent(
            task=TASK_PROMPT,
            llm=llm,
            controller=controller,
            browser=browser,
            max_actions_per_step=5,
        )

        print("\nAgent is navigating BuckeyeLink...")
        result = await agent.run(max_steps=30)

        # Print the raw holds text
        final = result.final_result() or "(no result returned)"
        print("\n" + "=" * 55)
        print("  HOLDS")
        print("=" * 55)
        print(final)
        print("=" * 55)

    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        print("Closing browser...")
        await browser.stop()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
