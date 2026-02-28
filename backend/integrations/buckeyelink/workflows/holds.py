"""
holds.py — Check Holds / To-Do Items Workflow

Navigates to the student's holds and to-do items to check for:
  - Service indicators (holds) blocking registration, transcripts, etc.
  - To-do list items that need action
  - Important deadlines and alerts

Pattern:
  - Browser is already on Student Hub (handled by auth)
  - AI Agent: navigate to holds/to-do, extract, and summarize
"""

import json
from pathlib import Path
from browser_use import Agent, BrowserSession, Controller, ActionResult
from backend.integrations.buckeyelink.config import get_llm


controller = Controller()


@controller.action("Save holds and to-do summary to file")
async def save_holds_json(holds_data: str) -> ActionResult:
    """Save extracted holds/to-do data to a local JSON file."""
    output_path = Path("output/holds_todo.json")
    output_path.parent.mkdir(exist_ok=True)

    try:
        parsed = json.loads(holds_data)
        output_path.write_text(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        output_path.write_text(holds_data)

    print(f"\nHolds/To-Do summary saved to {output_path}")
    return ActionResult(extracted_content=f"Holds/To-Do saved to {output_path}")


@controller.action("Ask user if they want to save holds data")
async def ask_save_holds() -> ActionResult:
    """Ask user if they want to save the holds/to-do summary."""
    choice = input("\nWould you like to save this summary to a file? (yes/no): ").strip().lower()
    if choice in ("yes", "y"):
        return ActionResult(extracted_content="User wants to save. Call save_holds_json.")
    return ActionResult(extracted_content="User does not want to save. Done.")


async def run_holds(browser_session: BrowserSession):
    """
    Run the holds / to-do items checking workflow.
    Browser is already authenticated and on the Student Hub.
    """
    print("\nStarting Holds / To-Do workflow...")

    llm = get_llm()

    agent = Agent(
        task="""
        You are helping a student check their holds and to-do items on BuckeyeLink (Ohio State University).
        The browser is currently on the BuckeyeLink Student Hub page, already authenticated.

        Steps:
        1. Navigate to the holds and to-do section from the Student Hub. Look for:
           - A "Holds" or "To Do" tile on the Student Hub
           - "Student Center" → look for "Holds", "Service Indicators", or "To Do List"
           - An alert banner or notification area showing holds
           - "Action Items" or "Tasks" section
           - If there's a navigation menu/sidebar, check under "Personal" or "Student Center"

        2. Extract ALL holds (service indicators). For each hold:
           - Hold type/name (e.g., "Bursar Hold", "Advising Hold", "Immunization Hold")
           - What it blocks (e.g., "Registration", "Transcript", "Diploma")
           - Department that placed the hold
           - Date placed
           - Any instructions for resolving it
           - Contact info if available

        3. Extract ALL to-do list items. For each item:
           - Item name/description
           - Due date (if any)
           - Status (completed, pending, overdue)
           - Any link or instruction for completing it

        4. Look for any alerts, notifications, or important messages on the page.

        5. Present everything in a clear, organized summary:

           === HOLDS ===
           (these block certain services until resolved)

           1. Bursar Hold
              Blocks: Registration, Transcript
              Placed by: Office of the Bursar
              Since: Jan 15, 2026
              To resolve: Pay outstanding balance at go.osu.edu/payonline

           2. (none — you have no holds!)

           === TO-DO LIST ===

           1. Complete FAFSA 2026-2027
              Due: March 1, 2026
              Status: Pending

           2. (all items completed!)

           === ALERTS ===
           (any important messages or deadlines)

        6. Call 'ask_save_holds' to see if user wants to save.
           If yes, call 'save_holds_json' with a JSON structure like:
           {
             "holds": [
               {"name": "Bursar Hold", "blocks": ["Registration", "Transcript"],
                "department": "Office of the Bursar", "date_placed": "2026-01-15",
                "resolution": "Pay outstanding balance"}
             ],
             "todo_items": [
               {"name": "Complete FAFSA", "due_date": "2026-03-01", "status": "Pending"}
             ],
             "alerts": ["Spring 2026 registration opens Feb 20"]
           }

        IMPORTANT:
        - The site uses PeopleSoft, so expect iframes and dynamic loading.
        - Wait for pages to load after clicking — PeopleSoft is slow.
        - If there are no holds, clearly state "No holds found" — this is good news!
        - If there are no to-do items, clearly state that too.
        - Be thorough — check multiple sections, as holds and to-do items
          may be on different pages.
        """,
        llm=llm,
        controller=controller,
        browser=browser_session,
        max_actions_per_step=5,
    )

    result = await agent.run(max_steps=25)
    print("\nHolds / To-Do workflow complete.")
    return result
