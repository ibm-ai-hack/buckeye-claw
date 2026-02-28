"""
main.py — BuckeyeLink Automation CLI

Usage:
    python main.py              # Interactive menu
    python main.py enroll       # Jump straight to enrollment
    python main.py grades       # Jump straight to grades
    python main.py financial    # Jump straight to financial
    python main.py schedule     # Jump straight to schedule
    python main.py holds        # Jump straight to holds / to-do
"""

import asyncio
import sys

from browser_use import BrowserSession

from backend.integrations.buckeyelink.config import HEADLESS
from backend.integrations.buckeyelink.auth import login


# ─── Workflow Registry ─────────────────────────────────────────────
WORKFLOWS = {
    "enroll": {
        "name": "Class Enrollment / Schedule Planning",
        "module": "backend.integrations.buckeyelink.workflows.enroll",
        "func": "run_enrollment",
    },
    "grades": {
        "name": "Check Grades / Transcript",
        "module": "backend.integrations.buckeyelink.workflows.grades",
        "func": "run_grades",
    },
    "financial": {
        "name": "Financial Aid / Billing",
        "module": "backend.integrations.buckeyelink.workflows.financial",
        "func": "run_financial",
    },
    "schedule": {
        "name": "View Class Schedule",
        "module": "backend.integrations.buckeyelink.workflows.schedule",
        "func": "run_schedule",
    },
    "holds": {
        "name": "Check Holds / To-Do Items",
        "module": "backend.integrations.buckeyelink.workflows.holds",
        "func": "run_holds",
    },
}


def show_menu() -> str:
    """Display workflow selection menu and return choice."""
    print()
    print("=" * 55)
    print("  BuckeyeLink Automation")
    print("=" * 55)
    print()

    for i, (key, wf) in enumerate(WORKFLOWS.items(), 1):
        print(f"  {i}. {wf['name']}  ({key})")

    print(f"  {len(WORKFLOWS) + 1}. Exit")
    print()

    choice = input("Select a workflow (number or name): ").strip().lower()

    # Accept number or key name
    if choice.isdigit():
        idx = int(choice) - 1
        keys = list(WORKFLOWS.keys())
        if 0 <= idx < len(keys):
            return keys[idx]
        elif idx == len(keys):
            return "exit"
    elif choice in WORKFLOWS:
        return choice

    print("Invalid choice, try again.")
    return show_menu()


async def main():
    # ── Parse CLI args ─────────────────────────────────────────────
    workflow_key = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in WORKFLOWS:
            workflow_key = arg
        else:
            print(f"Unknown workflow: {arg}")
            print(f"Available: {', '.join(WORKFLOWS.keys())}")
            sys.exit(1)

    # ── Interactive menu if no CLI arg ─────────────────────────────
    if not workflow_key:
        workflow_key = show_menu()
        if workflow_key == "exit":
            print("Bye!")
            return

    wf = WORKFLOWS[workflow_key]
    print(f"\n  Running: {wf['name']}")

    # ── Set up browser ─────────────────────────────────────────────
    browser = BrowserSession(
        headless=HEADLESS,
        disable_security=False,
        window_size={"width": 1280, "height": 900},
    )

    try:
        # Start the browser session and get a Playwright page
        await browser.start()
        page = await browser.get_current_page()

        # ── Authenticate ───────────────────────────────────────────
        logged_in = await login(page)
        if not logged_in:
            print("Login failed. Exiting.")
            return

        # ── Run the selected workflow ──────────────────────────────
        import importlib

        mod = importlib.import_module(wf["module"])
        run_func = getattr(mod, wf["func"])
        await run_func(browser)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        # ── Cleanup ────────────────────────────────────────────────
        print("\nClosing browser...")
        await browser.stop()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
