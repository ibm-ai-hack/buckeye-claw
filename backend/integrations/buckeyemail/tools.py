"""BeeAI tool wrappers for BuckeyeMail (Microsoft Graph email)."""

import re

from beeai_framework.tools import StringToolOutput, tool

from backend.integrations.buckeyemail.auth import build_auth_url, get_access_token
from backend.integrations.buckeyemail.client import (
    get_email_detail as _get_detail,
    get_inbox as _get_inbox,
    get_unread_count as _get_unread,
    search_emails as _search,
)


def _onboarding_message(phone: str) -> str:
    url = build_auth_url(phone)
    return (
        "Your BuckeyeMail isn't connected yet. "
        "Tap this link to sign in with your OSU Microsoft account and "
        f"you'll be all set:\n{url}"
    )


def _format_message(msg: dict) -> str:
    sender = msg.get("from", {}).get("emailAddress", {})
    name = sender.get("name", sender.get("address", "Unknown"))
    subject = msg.get("subject", "(no subject)")
    preview = msg.get("bodyPreview", "")[:120]
    read = "" if msg.get("isRead") else " [NEW]"
    date = msg.get("receivedDateTime", "")[:16].replace("T", " ")
    return f"{read}{subject}\n  from: {name} | {date}\n  {preview}"


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


@tool
async def get_email_inbox(from_number: str) -> StringToolOutput:
    """Get recent BuckeyeMail inbox messages for the student. Pass the caller's phone number as from_number."""
    token = get_access_token(from_number)
    if not token:
        return StringToolOutput(_onboarding_message(from_number))

    messages = await _get_inbox(token, top=10)
    if not messages:
        return StringToolOutput("Your inbox is empty!")

    lines = [_format_message(m) for m in messages]
    result = "Recent emails:\n\n" + "\n\n".join(lines)
    if len(result) > 1400:
        result = result[:1400] + "\n... (truncated)"
    return StringToolOutput(result)


@tool
async def search_emails(from_number: str, query: str) -> StringToolOutput:
    """Search BuckeyeMail by keyword, sender, or subject. Pass the caller's phone number as from_number."""
    token = get_access_token(from_number)
    if not token:
        return StringToolOutput(_onboarding_message(from_number))

    messages = await _search(token, query, top=10)
    if not messages:
        return StringToolOutput(f'No emails found matching "{query}".')

    lines = [_format_message(m) for m in messages]
    result = f'Search results for "{query}":\n\n' + "\n\n".join(lines)
    if len(result) > 1400:
        result = result[:1400] + "\n... (truncated)"
    return StringToolOutput(result)


@tool
async def get_unread_email_count(from_number: str) -> StringToolOutput:
    """Get the number of unread BuckeyeMail messages. Pass the caller's phone number as from_number."""
    token = get_access_token(from_number)
    if not token:
        return StringToolOutput(_onboarding_message(from_number))

    count = await _get_unread(token)
    if count == 0:
        return StringToolOutput("You have no unread emails — inbox zero!")
    return StringToolOutput(f"You have {count} unread email{'s' if count != 1 else ''}.")


@tool
async def get_email_detail(from_number: str, message_id: str) -> StringToolOutput:
    """Get the full body of a specific email by message ID. Pass the caller's phone number as from_number."""
    token = get_access_token(from_number)
    if not token:
        return StringToolOutput(_onboarding_message(from_number))

    msg = await _get_detail(token, message_id)
    sender = msg.get("from", {}).get("emailAddress", {})
    name = sender.get("name", sender.get("address", "Unknown"))
    subject = msg.get("subject", "(no subject)")
    date = msg.get("receivedDateTime", "")[:16].replace("T", " ")
    attachments = " [has attachments]" if msg.get("hasAttachments") else ""

    body_obj = msg.get("body", {})
    body = body_obj.get("content", "")
    if body_obj.get("contentType") == "html":
        body = _strip_html(body)

    result = f"Subject: {subject}\nFrom: {name}\nDate: {date}{attachments}\n\n{body}"
    if len(result) > 1400:
        result = result[:1400] + "\n... (truncated)"
    return StringToolOutput(result)
