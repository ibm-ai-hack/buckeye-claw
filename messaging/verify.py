import hashlib
import hmac
import time


def verify_webhook_signature(
    raw_body: str,
    signature: str | None,
    timestamp: str | None,
    secret: str,
    max_age_seconds: float = 300,
) -> tuple[bool, str | None]:
    """Verify a Linq webhook HMAC-SHA256 signature.

    Returns (True, None) on success or (False, reason) on failure.
    """
    if not signature:
        return False, "missing X-Webhook-Signature header"
    if not timestamp:
        return False, "missing X-Webhook-Timestamp header"

    try:
        ts = float(timestamp)
    except (ValueError, TypeError):
        return False, "invalid timestamp"

    now = time.time()
    if abs(now - ts) > max_age_seconds:
        return False, "timestamp too old or too far in the future"

    # Linq signed payload format: "{timestamp}.{rawBody}"
    expected = hmac.new(
        secret.encode(), f"{timestamp}.{raw_body}".encode(), hashlib.sha256
    ).hexdigest()

    # Strip optional "sha256=" prefix
    provided = signature.removeprefix("sha256=")

    if not hmac.compare_digest(expected, provided):
        return False, "signature mismatch"

    return True, None
