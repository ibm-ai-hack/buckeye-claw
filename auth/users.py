import logging

from supabase import Client

logger = logging.getLogger(__name__)


def get_or_create_user(client: Client, phone: str) -> str:
    """Resolve a phone number to a profile ID, creating a profile if needed.

    Args:
        client: Supabase service-role client.
        phone: E.164 phone number, e.g. "+16141234567".

    Returns:
        The profile UUID as a string.
    """
    result = (
        client.table("profiles")
        .select("id")
        .eq("phone", phone)
        .maybe_single()
        .execute()
    )

    if result is not None and result.data:
        return result.data["id"]

    # Profile doesn't exist — create one.
    insert_result = (
        client.table("profiles")
        .insert({"phone": phone})
        .execute()
    )
    user_id: str = insert_result.data[0]["id"]
    logger.info("Created new profile for phone %s → %s", phone, user_id)
    return user_id


def get_user_by_id(client: Client, user_id: str) -> dict | None:
    """Fetch a profile by its UUID.

    Args:
        client: Supabase service-role client.
        user_id: Profile UUID string.

    Returns:
        Profile dict with keys (id, phone, email, auth_id, created_at, updated_at),
        or None if not found.
    """
    result = (
        client.table("profiles")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    return result.data if result is not None else None
