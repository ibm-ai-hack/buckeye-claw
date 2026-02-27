"""
enroll.py — Class Enrollment Workflow

This is the most dynamic workflow, so it leans heavily on the AI agent.
The enrollment forms at OSU have dynamic dropdowns, AJAX-loaded sections,
and multi-step confirmation flows that change by term.

Pattern:
  - Deterministic: navigate to the Student Hub (already done by auth)
  - AI Agent: handle search, selection, cart, and confirmation
  - Safety gate: always confirm before enrolling
"""

from browser_use import Agent, BrowserSession, Controller, ActionResult
from config import get_llm


# ─── Controller with custom actions ────────────────────────────────
controller = Controller()


@controller.action("Ask user to confirm enrollment before submitting")
async def confirm_enrollment(classes: str) -> ActionResult:
    """
    Safety gate: always ask the user before actually enrolling.
    The AI agent will call this before clicking the final 'Enroll' button.
    """
    print("\n" + "=" * 55)
    print("  ENROLLMENT CONFIRMATION")
    print("=" * 55)
    print(f"The agent wants to enroll you in:\n{classes}")
    print("=" * 55)

    response = input("\nType 'yes' to confirm enrollment, anything else to cancel: ").strip().lower()

    if response == "yes":
        return ActionResult(extracted_content="User confirmed enrollment. Proceed with enrollment.")
    else:
        return ActionResult(extracted_content="User cancelled enrollment. Do NOT click enroll. Stop here.")


@controller.action("Ask user for class search details")
async def get_class_info() -> ActionResult:
    """Prompt user for what class they want to enroll in."""
    print("\nWhat class are you looking for?")
    subject = input("  Subject (e.g., CSE, MATH, ECON): ").strip()
    catalog_num = input("  Catalog number (e.g., 2221, 1151): ").strip()
    term = input("  Term (e.g., Spring 2026, Autumn 2025) [leave blank for current]: ").strip()

    search = f"Subject: {subject}, Catalog Number: {catalog_num}"
    if term:
        search += f", Term: {term}"

    return ActionResult(extracted_content=f"Search for: {search}")


@controller.action("Ask user to pick a section from a list")
async def pick_section(sections_summary: str) -> ActionResult:
    """Let the user choose which section to enroll in."""
    print("\nAvailable sections:")
    print(sections_summary)
    choice = input("\nEnter the section number you want (or 'cancel' to stop): ").strip()

    if choice.lower() == "cancel":
        return ActionResult(extracted_content="User cancelled. Stop the enrollment process.")

    return ActionResult(extracted_content=f"User selected section: {choice}")


async def run_enrollment(browser_session: BrowserSession):
    """
    Run the class enrollment workflow.

    Uses a hybrid approach:
    - The browser is already authenticated and on the Student Hub
    - AI agent handles the dynamic search/selection/enrollment forms
    """
    print("\nStarting Class Enrollment workflow...")

    # ── AI Agent: Handle the dynamic enrollment flow ───────────────
    llm = get_llm()

    agent = Agent(
        task="""
        You are helping a student enroll in classes on BuckeyeLink (Ohio State University).
        The browser is currently on the BuckeyeLink Student Hub page, already authenticated.

        Steps:
        1. First, call 'get_class_info' to ask the user what class they want.
        2. Navigate to the enrollment/class search section from the Student Hub.
           Look for links or tiles like:
           - "Manage Classes" or "Enroll"
           - "Class Search" or "Search for Classes"
           - "Schedule" or "Plan My Schedule"
           - Links within the "Academics" section
           - If you see a navigation sidebar, look for enrollment options there
        3. If there's a term selector, choose the correct term based on user input.
        4. Search for the class the user specified using the subject and catalog number.
        5. When results appear, extract section details:
           - Section number, class number
           - Days/times
           - Instructor name
           - Location/room
           - Open seats / enrollment capacity
           - Waitlist info if applicable
        6. If multiple sections are available, call 'pick_section' with a formatted
           summary so the user can choose.
        7. Add the selected section to the enrollment cart.
        8. BEFORE clicking the final enroll/submit button, call 'confirm_enrollment'
           with a clear summary of what will be enrolled (class, section, time, instructor).
        9. Only proceed with enrollment if the user confirms.

        IMPORTANT:
        - Never enroll without calling confirm_enrollment first.
        - If you encounter errors (class full, time conflict, prerequisite issue),
          describe them clearly to the user.
        - The site uses PeopleSoft, so expect iframes and dynamic content.
        - If you see a "Student Center" or "PeopleSoft" iframe, interact with
          elements inside it.
        - Wait for pages to load after clicking — PeopleSoft is slow.
        """,
        llm=llm,
        controller=controller,
        browser=browser_session,
        max_actions_per_step=5,
    )

    result = await agent.run(max_steps=30)
    print("\nEnrollment workflow complete.")
    return result
