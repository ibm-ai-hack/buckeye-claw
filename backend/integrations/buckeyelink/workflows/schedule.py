"""
schedule.py — View Class Schedule Workflow

Navigates to the student's class schedule and extracts:
  - All enrolled classes for the selected term
  - Days, times, locations, and instructors
  - Optionally saves to a file or prints a weekly grid

Pattern:
  - Browser is already on Student Hub (handled by auth)
  - AI Agent: navigate to schedule, extract, and format
"""

import json
from pathlib import Path
from browser_use import Agent, BrowserSession, Controller, ActionResult
from backend.integrations.buckeyelink.config import get_llm


controller = Controller()


@controller.action("Save schedule to a JSON file")
async def save_schedule_json(schedule_data: str) -> ActionResult:
    """Save extracted schedule to a local JSON file."""
    output_path = Path("output/schedule.json")
    output_path.parent.mkdir(exist_ok=True)

    try:
        parsed = json.loads(schedule_data)
        output_path.write_text(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        output_path.write_text(schedule_data)

    print(f"\nSchedule saved to {output_path}")
    return ActionResult(extracted_content=f"Schedule saved to {output_path}")


@controller.action("Ask user which term's schedule to view")
async def get_schedule_term() -> ActionResult:
    """Ask which semester's schedule to view."""
    print("\nWhich term's schedule do you want to see?")
    print("  1. Current term")
    print("  2. Next term (upcoming)")
    print("  3. Specific term (I'll type it)")

    choice = input("\n  Enter choice (1-3): ").strip()

    if choice == "1":
        return ActionResult(extracted_content="Show the class schedule for the current term.")
    elif choice == "2":
        return ActionResult(extracted_content="Show the class schedule for the next/upcoming term.")
    elif choice == "3":
        term = input("  Enter term (e.g., Autumn 2025, Spring 2026): ").strip()
        return ActionResult(extracted_content=f"Show the class schedule for: {term}")
    else:
        return ActionResult(extracted_content="Show the class schedule for the current term.")


@controller.action("Ask user if they want to save schedule to file")
async def ask_save_schedule() -> ActionResult:
    """Ask user if they want to save the extracted schedule."""
    choice = input("\nWould you like to save this schedule to a file? (yes/no): ").strip().lower()
    if choice in ("yes", "y"):
        return ActionResult(extracted_content="User wants to save. Call save_schedule_json.")
    return ActionResult(extracted_content="User does not want to save. Done.")


async def run_schedule(browser_session: BrowserSession):
    """
    Run the class schedule viewing workflow.
    Browser is already authenticated and on the Student Hub.
    """
    print("\nStarting Schedule workflow...")

    llm = get_llm()

    agent = Agent(
        task="""
        You are helping a student view their class schedule on BuckeyeLink (Ohio State University).
        The browser is currently on the BuckeyeLink Student Hub page, already authenticated.

        Steps:
        1. Call 'get_schedule_term' to ask the user which term they want.
        2. Navigate to the schedule section from the Student Hub. Look for:
           - A "Schedule" or "My Schedule" tile on the Student Hub
           - "Student Center" → "Academics" → "My Class Schedule"
           - "Weekly Schedule" or "View My Classes"
           - "Manage Classes" → "My Class Schedule"
           - If there's a navigation menu/sidebar, check under "Academics"
        3. Select the correct term if a term dropdown appears.
        4. Extract the FULL schedule. For each class, get:
           - Course code and number (e.g., CSE 2221)
           - Course title (e.g., Software I: Software Components)
           - Section number
           - Days (e.g., MWF, TR)
           - Start time and end time (e.g., 9:10 AM - 10:05 AM)
           - Location/building and room number
           - Instructor name
           - Credits
           - Status (enrolled, waitlisted, etc.)
        5. Present the schedule in a clean format organized by day:

           --- MONDAY / WEDNESDAY / FRIDAY ---
           9:10 AM - 10:05 AM  |  CSE 2221 (Section 0010)  |  Dreese Lab 264  |  Prof. Smith
           11:30 AM - 12:25 PM |  MATH 2153 (Section 0020) |  Enarson 214     |  Prof. Jones

           --- TUESDAY / THURSDAY ---
           1:00 PM - 2:20 PM   |  ECON 2001 (Section 0030) |  Mendenhall 100  |  Prof. Lee

           Total Credits: 16

        6. Call 'ask_save_schedule' to see if user wants to save.
           If yes, call 'save_schedule_json' with a JSON structure like:
           {
             "term": "Spring 2026",
             "total_credits": 16,
             "classes": [
               {
                 "code": "CSE 2221",
                 "title": "Software I: Software Components",
                 "section": "0010",
                 "days": "MWF",
                 "start_time": "9:10 AM",
                 "end_time": "10:05 AM",
                 "location": "Dreese Lab 264",
                 "instructor": "Prof. Smith",
                 "credits": 4,
                 "status": "Enrolled"
               }
             ]
           }

        IMPORTANT:
        - The site uses PeopleSoft, so expect iframes and dynamic loading.
        - Wait for pages to load after clicking — PeopleSoft is slow.
        - If the schedule view has a "list" vs "weekly" toggle, either view works.
        - If no classes are enrolled for the selected term, say so clearly.
        """,
        llm=llm,
        controller=controller,
        browser=browser_session,
        max_actions_per_step=5,
    )

    result = await agent.run(max_steps=25)
    print("\nSchedule workflow complete.")
    return result
