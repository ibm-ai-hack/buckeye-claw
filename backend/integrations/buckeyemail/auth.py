"""MSAL OAuth flows for BuckeyeMail (Microsoft 365 / Graph API)."""

import os
from urllib.parse import quote

import msal

from backend.integrations.buckeyemail.token_store import (
    load_token_cache,
    save_token_cache,
)

SCOPES = ["Mail.Read", "Mail.ReadBasic", "offline_access", "User.Read"]


def _client_id() -> str:
    return os.environ["AZURE_CLIENT_ID"]


def _client_secret() -> str:
    return os.environ["AZURE_CLIENT_SECRET"]


def _redirect_uri() -> str:
    return os.environ["AZURE_REDIRECT_URI"]


def _build_cache(phone: str) -> msal.SerializableTokenCache:
    """Load (or create) an MSAL token cache for the given phone number."""
    cache = msal.SerializableTokenCache()
    data = load_token_cache(phone)
    if data:
        cache.deserialize(data)
    return cache


def _save_cache(phone: str, cache: msal.SerializableTokenCache) -> None:
    """Persist the MSAL cache if it changed."""
    if cache.has_state_changed:
        save_token_cache(phone, cache.serialize())


def get_msal_app(
    cache: msal.SerializableTokenCache | None = None,
) -> msal.ConfidentialClientApplication:
    """Create an MSAL ConfidentialClientApplication."""
    return msal.ConfidentialClientApplication(
        client_id=_client_id(),
        client_credential=_client_secret(),
        authority="https://login.microsoftonline.com/common",
        token_cache=cache,
    )


def build_auth_url(phone: str) -> str:
    """Generate the Microsoft OAuth authorization URL.

    The user's phone number is passed in the ``state`` parameter so the
    callback can associate the resulting tokens with the right user.
    """
    app = get_msal_app()
    auth_url = app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=_redirect_uri(),
        state=quote(phone, safe=""),
    )
    return auth_url


def exchange_code_for_tokens(code: str, phone: str) -> dict:
    """Exchange an authorization code for access + refresh tokens and persist them."""
    cache = _build_cache(phone)
    app = get_msal_app(cache)
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=_redirect_uri(),
    )
    _save_cache(phone, cache)
    return result


def get_access_token(phone: str) -> str | None:
    """Return a valid access token for *phone*, refreshing silently if needed.

    Returns ``None`` if the user has not connected BuckeyeMail.
    """
    cache = _build_cache(phone)
    if not cache.has_state_changed and load_token_cache(phone) is None:
        return None

    app = get_msal_app(cache)
    accounts = app.get_accounts()
    if not accounts:
        return None

    result = app.acquire_token_silent(SCOPES, account=accounts[0])
    _save_cache(phone, cache)

    if result and "access_token" in result:
        return result["access_token"]
    return None
