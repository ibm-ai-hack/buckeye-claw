"""
Claude-powered prompt enhancer for BuckeyeLink queries.

Takes a vague user request (e.g. "what's my tuition bill?") and produces
precise browser navigation + extraction instructions for the browser-use agent.
"""

import logging

from beeai_framework.backend import ChatModel
from beeai_framework.backend.message import UserMessage, SystemMessage

from backend.integrations.buckeyelink.knowledge import KNOWN_PAGES, SITEMAP_HINTS, PEOPLESOFT_KNOWLEDGE

logger = logging.getLogger(__name__)

# Build the knowledge context once at module level
_PAGES_SECTION = "\n".join(
    f"- **{key}**: {info['description']} → `{info['url']}`"
    for key, info in KNOWN_PAGES.items()
)

_HINTS_SECTION = "\n".join(
    f"- **{key}**: {info['description']}\n  Navigation: {info['nav_hint']}"
    for key, info in SITEMAP_HINTS.items()
)

_SYSTEM_PROMPT = f"""\
You are a prompt engineer that converts vague student requests into precise \
browser automation instructions for navigating BuckeyeLink (Ohio State University's \
student portal).

{PEOPLESOFT_KNOWLEDGE}

## Known Pages (direct URLs available)
{_PAGES_SECTION}

## Pages Without Direct URLs (navigation hints)
{_HINTS_SECTION}

## Your Task

Given a student's request, produce a structured instruction for a browser automation \
agent. The browser is ALREADY authenticated and on buckeyelink.osu.edu. \
The agent can navigate, click, scroll, and read page content.

Your output MUST follow this exact format:

NAVIGATION:
[Step-by-step instructions to reach the right page. If a direct URL exists, say \
"Navigate to <url>". Otherwise, give click-by-click navigation from the dashboard.]

EXTRACTION:
[What specific data to extract from the page. Be precise — field names, table columns, \
section headers to look for.]

FORMAT:
[How to format the extracted data for the user. Keep it concise and readable.]

Rules:
- This is READ-ONLY. Never instruct the agent to click submit, enroll, drop, pay, or \
modify any data.
- If the request is ambiguous, make reasonable assumptions for an OSU student.
- If a term/semester might be relevant, default to the current or most recent term.
- Always instruct the agent to wait for page loads and check inside iframes.
"""


async def enhance_prompt(user_request: str) -> str:
    """Enhance a vague user request into precise browser automation instructions.

    Args:
        user_request: The raw user question (e.g. "what's my tuition?")

    Returns:
        Enhanced prompt with NAVIGATION/EXTRACTION/FORMAT sections,
        wrapped with safety guards.
    """
    llm = ChatModel.from_name("anthropic:claude-sonnet-4")

    response = await llm.create(
        messages=[
            SystemMessage(content=_SYSTEM_PROMPT),
            UserMessage(content=user_request),
        ],
    )

    enhanced = response.get_text_content()
    logger.info("Enhanced prompt for request: %s", user_request[:80])
    logger.debug("Enhanced prompt:\n%s", enhanced)

    # Wrap with preamble and safety guard
    return (
        "The browser is already authenticated on buckeyelink.osu.edu. "
        "Do NOT attempt to log in or enter credentials.\n\n"
        f"{enhanced}\n\n"
        "IMPORTANT: This is READ-ONLY. Do NOT click any buttons that submit, "
        "enroll, drop, pay, or modify data. Only navigate and extract information."
    )
