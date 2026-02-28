"""Microsoft Graph API client for BuckeyeMail."""

import httpx

BASE_URL = "https://graph.microsoft.com/v1.0"

_MAIL_FIELDS = "subject,from,receivedDateTime,bodyPreview,isRead"


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def get_inbox(access_token: str, top: int = 10) -> list[dict]:
    """Fetch the most recent inbox messages."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/me/messages",
            headers=_headers(access_token),
            params={
                "$top": top,
                "$orderby": "receivedDateTime desc",
                "$select": _MAIL_FIELDS,
            },
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


async def search_emails(access_token: str, query: str, top: int = 10) -> list[dict]:
    """Search inbox messages by keyword, sender, or subject."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/me/messages",
            headers=_headers(access_token),
            params={
                "$search": f'"{query}"',
                "$top": top,
                "$select": _MAIL_FIELDS,
            },
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


async def get_unread_count(access_token: str) -> int:
    """Return the number of unread messages in the inbox."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/me/mailFolders/inbox",
            headers=_headers(access_token),
            params={"$select": "unreadItemCount"},
        )
        resp.raise_for_status()
        return resp.json().get("unreadItemCount", 0)


async def get_email_detail(access_token: str, message_id: str) -> dict:
    """Fetch the full detail of a single email."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/me/messages/{message_id}",
            headers=_headers(access_token),
            params={
                "$select": "subject,from,body,receivedDateTime,hasAttachments",
            },
        )
        resp.raise_for_status()
        return resp.json()
