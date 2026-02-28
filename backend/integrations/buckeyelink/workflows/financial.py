"""
financial.py — Financial Aid & Billing Workflow

Navigates the financial sections of BuckeyeLink to extract:
  - Current account balance
  - Financial aid awards and status
  - Tuition charges breakdown
  - Payment due dates

Pattern:
  - Browser is already on Student Hub (handled by auth)
  - AI Agent: navigate financial pages and extract data
"""

import json
from pathlib import Path
from browser_use import Agent, BrowserSession, Controller, ActionResult
from backend.integrations.buckeyelink.config import get_llm


controller = Controller()


@controller.action("Save financial summary to file")
async def save_financial_json(financial_data: str) -> ActionResult:
    """Save extracted financial info to a local JSON file."""
    output_path = Path("output/financial_summary.json")
    output_path.parent.mkdir(exist_ok=True)

    try:
        parsed = json.loads(financial_data)
        output_path.write_text(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        output_path.write_text(financial_data)

    print(f"\nFinancial summary saved to {output_path}")
    return ActionResult(extracted_content=f"Financial summary saved to {output_path}")


@controller.action("Ask user what financial info they need")
async def get_financial_preference() -> ActionResult:
    """Ask the user what financial information they're looking for."""
    print("\nWhat financial information do you need?")
    print("  1. Current account balance & charges")
    print("  2. Financial aid awards & status")
    print("  3. Payment due dates & history")
    print("  4. Full overview (all of the above)")

    choice = input("\n  Enter choice (1-4): ").strip()

    mapping = {
        "1": "Show the current account balance, tuition charges, and any fees.",
        "2": "Show financial aid awards, their status (accepted/pending/disbursed), and amounts.",
        "3": "Show payment due dates, any past payments, and payment plan details if applicable.",
        "4": "Show a complete financial overview: balance, charges, financial aid awards and status, and payment due dates.",
    }

    return ActionResult(
        extracted_content=mapping.get(choice, mapping["4"])
    )


@controller.action("Ask user if they want to save financial data")
async def ask_save_financial() -> ActionResult:
    """Ask user if they want to save the extracted financial data."""
    choice = input("\nWould you like to save this financial summary to a file? (yes/no): ").strip().lower()
    if choice in ("yes", "y"):
        return ActionResult(extracted_content="User wants to save. Call save_financial_json.")
    return ActionResult(extracted_content="User does not want to save. Done.")


async def run_financial(browser_session: BrowserSession):
    """
    Run the financial aid / billing workflow.
    Browser is already authenticated and on the Student Hub.
    """
    print("\nStarting Financial workflow...")

    llm = get_llm()

    agent = Agent(
        task="""
        You are helping a student check their financial information on BuckeyeLink (Ohio State University).
        The browser is currently on the BuckeyeLink Student Hub page, already authenticated.

        Steps:
        1. Call 'get_financial_preference' to ask what info the user needs.
        2. Navigate to the financial section from the Student Hub. Look for:
           - A "Finances" or "Financial" tile on the Student Hub
           - "Student Center" → "Finances" tab or section
           - "Account Balance" or "View Account"
           - "Financial Aid" or "View Financial Aid"
           - "Make a Payment" or "Statement of Account"
           - If there's a navigation menu/sidebar, check under "Finances"
        3. Based on user preference, extract the relevant information:

           For ACCOUNT BALANCE:
           - Total amount due
           - Itemized charges (tuition, fees, housing, meal plan, etc.)
           - Any credits or payments already applied
           - Due date for next payment

           For FINANCIAL AID:
           - Each award: name, amount, status (offered/accepted/disbursed)
           - Total aid package amount
           - Expected disbursement dates
           - Any action items (e.g., forms to complete, verification needed)
           - Satisfactory academic progress status if visible

           For PAYMENT INFO:
           - Next payment due date and amount
           - Payment plan details if enrolled
           - Recent payment history (last 3-5 payments)
           - Any late fees or holds

        4. Present everything in a clear, formatted summary in your response.
           Use clear sections with headers, like:
           --- Account Balance ---
           Total Due: $5,234.00 (due March 15, 2026)
           ... etc.

        5. Call 'ask_save_financial' to see if user wants to save.
           If yes, call 'save_financial_json' with a JSON structure like:
           {
             "balance": {"total_due": 5234.00, "due_date": "2026-03-15"},
             "charges": [{"description": "Tuition", "amount": 5000.00}],
             "financial_aid": [{"name": "Pell Grant", "amount": 3000.00, "status": "Disbursed"}],
             "payments": [{"date": "2026-01-15", "amount": 2500.00, "method": "e-check"}]
           }

        IMPORTANT:
        - Financial data is sensitive — be accurate, don't guess amounts.
        - The site uses PeopleSoft, so expect iframes and dynamic loading.
        - Wait for pages to load after clicking — PeopleSoft is slow.
        - If some sections require additional navigation, follow through.
        - Report exact dollar amounts as they appear on screen.
        """,
        llm=llm,
        controller=controller,
        browser=browser_session,
        max_actions_per_step=5,
    )

    result = await agent.run(max_steps=30)
    print("\nFinancial workflow complete.")
    return result
