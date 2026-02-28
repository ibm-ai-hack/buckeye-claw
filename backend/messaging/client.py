import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.linqapp.com/api/partner/v3"
_TIMEOUT = 15.0
_MAX_RETRIES = 3


class LinqClient:
    """Async HTTP client for the Linq Partner API v3."""

    def __init__(self, api_token: str, base_url: str = _BASE_URL):
        self._token = api_token
        self._base_url = base_url.rstrip("/")
        self._http: httpx.AsyncClient | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                timeout=_TIMEOUT,
            )
        return self._http

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        client = await self._client()
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                resp = await client.request(method, path, **kwargs)
                if resp.status_code == 429 or resp.status_code >= 500:
                    wait = 2**attempt
                    logger.warning(
                        "Linq API %s %s returned %d, retrying in %ds",
                        method, path, resp.status_code, wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                if resp.status_code == 204:
                    return {}
                return resp.json()
            except httpx.HTTPStatusError as e:
                raise
            except httpx.HTTPError as e:
                last_exc = e
                wait = 2**attempt
                logger.warning("Linq API request error: %s, retrying in %ds", e, wait)
                await asyncio.sleep(wait)

        if last_exc:
            raise last_exc
        return {}

    # -- Chats --

    async def create_chat(self, from_number: str, to: list[str]) -> dict:
        return await self._request(
            "POST", "/chats", json={"from": from_number, "to": to}
        )

    # -- Messages --

    async def send_message(
        self, chat_id: str, parts: list[dict], service: str | None = None
    ) -> dict:
        body: dict = {"message": {"parts": parts}}
        if service:
            body["service"] = service
        return await self._request("POST", f"/chats/{chat_id}/messages", json=body)

    # -- Typing indicators --

    async def start_typing(self, chat_id: str) -> None:
        await self._request("POST", f"/chats/{chat_id}/typing")

    async def stop_typing(self, chat_id: str) -> None:
        await self._request("DELETE", f"/chats/{chat_id}/typing")

    # -- Read receipts --

    async def mark_read(self, chat_id: str) -> None:
        await self._request("POST", f"/chats/{chat_id}/read")

    # -- Reactions --

    async def add_reaction(self, message_id: str, reaction_type: str) -> None:
        await self._request(
            "POST",
            f"/messages/{message_id}/reactions",
            json={"operation": "add", "type": reaction_type},
        )

    async def remove_reaction(self, message_id: str, reaction_type: str) -> None:
        await self._request(
            "POST",
            f"/messages/{message_id}/reactions",
            json={"operation": "remove", "type": reaction_type},
        )

    # -- Webhook subscriptions --

    async def create_webhook_subscription(
        self, target_url: str, events: list[str]
    ) -> dict:
        return await self._request(
            "POST",
            "/webhook-subscriptions",
            json={"target_url": target_url, "subscribed_events": events},
        )

    async def list_webhook_subscriptions(self) -> dict:
        return await self._request("GET", "/webhook-subscriptions")

    async def delete_webhook_subscription(self, subscription_id: str) -> dict:
        return await self._request(
            "DELETE", f"/webhook-subscriptions/{subscription_id}"
        )

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
