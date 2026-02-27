import logging
import os

from supabase import Client, create_client

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    """Return a singleton Supabase client using the service role key.

    The service role key bypasses Row Level Security and is required for
    server-side operations (creating users, reading across all rows).
    Never expose this key in client-side code.
    """
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
        logger.debug("Supabase client initialized (URL: %s)", url)
    return _client
