"""
Standalone Linq SMS sender for the local Grubhub server.

Used by the scheduler to send order notifications without depending
on backend.messaging.chat_store (which only exists in the cloud).
"""

import os
import logging

import httpx

logger = logging.getLogger(__name__)

_LINQ_BASE = "https://api.linqapp.com/api/partner/v3"
_TIMEOUT = 15.0


async def send_sms(to: str, text: str) -> None:
    """Send an SMS notification via the Linq Partner API."""
    token = os.environ["LINQ_API_TOKEN"]
    from_number = os.environ["LINQ_FROM_NUMBER"]
    preferred = os.environ.get("LINQ_PREFERRED_SERVICE", "iMessage")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(
        base_url=_LINQ_BASE, headers=headers, timeout=_TIMEOUT
    ) as client:
        # Create or reuse a chat for this phone number
        resp = await client.post("/chats", json={"from": from_number, "to": [to]})
        resp.raise_for_status()
        chat_id = resp.json().get("chat", {}).get("id", "")

        if not chat_id:
            logger.error("Failed to create Linq chat for %s", to)
            return

        # Send the message
        await client.post(
            f"/chats/{chat_id}/messages",
            json={
                "message": {"parts": [{"type": "text", "value": text}]},
                "service": preferred,
            },
        )
        logger.info("Sent scheduled order notification to %s", to)
