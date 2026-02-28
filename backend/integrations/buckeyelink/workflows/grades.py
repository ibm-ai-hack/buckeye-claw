"""
grades.py — Check Grades / Transcript Workflow

Navigates the BuckeyeLink grades section and extracts grade data.

Pattern:
  - Browser is already on Student Hub (handled by auth)
  - AI Agent: navigate to grades, extract, format, and optionally save
"""

import json
from pathlib import Path
from browser_use import Agent, BrowserSession, Controller, ActionResult
from backend.integrations.buckeyelink.config import get_llm


controller = Controller()


@controller.action("Save grades to a JSON file")
async def save_grades_json(grades_data: str) -> ActionResult:
    """Save extracted grades to a local JSON file."""
    output_path = Path("output/grades.json")
    output_path.parent.mkdir(exist_ok=True)

    try:
        parsed = json.loads(grades_data)
        output_path.write_text(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        output_path.write_text(grades_data)

    print(f"\nGrades saved to {output_path}")
    return ActionResult(extracted_content=f"Grades saved to {output_path}")


@controller.action("Ask user which term to check grades for")
async def get_term_preference() -> ActionResult:
    """Ask which semester's grades to look at."""
    print("\nWhich term do you want to check grades for?")
    print("  1. Current term")
    print("  2. Most recent completed term")
    print("  3. All terms (unofficial transcript view)")
    print("  4. Specific term (I'll type it)")

    choice = input("\n  Enter choice (1-4): ").strip()

    if choice == "1":
        return ActionResult(extracted_content="Show grades for the current term.")
    elif choice == "2":
        return ActionResult(extracted_content="Show grades for the most recent completed term.")
    elif choice == "3":
        return ActionResult(extracted_content="Show the unofficial transcript / all terms.")
    elif choice == "4":
        term = input("  Enter term (e.g., Autumn 2025, Spring 2026): ").strip()
        return ActionResult(extracted_content=f"Show grades for: {term}")
    else:
        return ActionResult(extracted_content="Show grades for the current term.")


@controller.action("Ask user if they want to save grades to file")
async def ask_save_grades() -> ActionResult:
    """Ask user if they want to save the extracted grades."""
    choice = input("\nWould you like to save these grades to a file? (yes/no): ").strip().lower()
    if choice in ("yes", "y"):
        return ActionResult(extracted_content="User wants to save grades. Call save_grades_json.")
    return ActionResult(extracted_content="User does not want to save. Done.")


async def run_grades(browser_session: BrowserSession):
    """
    Run the grades checking workflow.
    Browser is already authenticated and on the Student Hub.
    """
    print("\nStarting Grades workflow...")

    llm = get_llm()

    agent = Agent(
        task="""
        You are helping a student check their grades on BuckeyeLink (Ohio State University).
        The browser is currently on the BuckeyeLink Student Hub page, already authenticated.

        Steps:
        1. Call 'get_term_preference' to ask the user which term they want.
        2. Navigate to the grades section from the Student Hub. Look for:
           - A "Grades" tile or link on the Student Hub
           - "Academics" section → "View Grades" or "Grades"
           - "Student Center" link → then find grades in the academics area
           - "View my grades" or "Unofficial Transcript"
           - If there's a navigation menu/sidebar, check under "Academics"
        3. Select the appropriate term based on user preference.
           - If a term dropdown appears, select the right one.
           - For "all terms", look for an unofficial transcript link.
        4. Extract ALL grade information visible:
           - Course code (e.g., CSE 2221)
           - Course title (e.g., Software I: Software Components)
           - Credits/units (e.g., 4.00)
           - Grade received (e.g., A, B+, IP for in-progress)
           - Term GPA and cumulative GPA if visible
        5. Present the grades in your response as a clean formatted list like:
           CSE 2221 - Software I: Software Components (4 cr) — A
           MATH 2153 - Calculus III (4 cr) — B+
           ... etc.
           Term GPA: 3.75 | Cumulative GPA: 3.65

        6. Call 'ask_save_grades' to see if user wants to save.
           If yes, call 'save_grades_json' with a JSON string like:
           {"term": "Autumn 2025", "courses": [{"code": "CSE 2221", "title": "Software I", "credits": 4, "grade": "A"}], "term_gpa": 3.75, "cumulative_gpa": 3.65}

        IMPORTANT:
        - The site uses PeopleSoft, so expect iframes and dynamic loading.
        - Wait for pages to load after clicking — PeopleSoft is slow.
        - If grades aren't posted yet for a term, say so clearly.
        - If you see "In Progress" or similar, report that as the grade status.
        """,
        llm=llm,
        controller=controller,
        browser=browser_session,
        max_actions_per_step=5,
    )

    result = await agent.run(max_steps=25)
    print("\nGrades workflow complete.")
    return result
