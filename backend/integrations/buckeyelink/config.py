"""
Configuration loader for BuckeyeLink automation.
Reads .env and sets up the LLM + browser config.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── OSU Credentials ───────────────────────────────────────────────
OSU_USERNAME = os.getenv("OSU_USERNAME", "")
OSU_PASSWORD = os.getenv("OSU_PASSWORD", "")

if not OSU_USERNAME or not OSU_PASSWORD:
    raise ValueError("Set OSU_USERNAME and OSU_PASSWORD in your .env file")

# ─── Duo MFA ───────────────────────────────────────────────────────
DUO_TIMEOUT = int(os.getenv("DUO_TIMEOUT", "120"))

# ─── Browser ───────────────────────────────────────────────────────
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))

# ─── LLM Setup ─────────────────────────────────────────────────────
def get_llm():
    """Return the configured LLM instance for Browser Use."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key:
        from browser_use import ChatAnthropic
        return ChatAnthropic(model="claude-sonnet-4-20250514")
    elif openai_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o")
    else:
        # Fall back to Browser Use's own model
        from browser_use import ChatBrowserUse
        return ChatBrowserUse()


# ─── URLs ──────────────────────────────────────────────────────────
BUCKEYELINK_URL = "https://buckeyelink.osu.edu/"
STUDENT_CENTER_URL = "https://buckeyelink.osu.edu/student-hub"
