import asyncio
import json
import logging
import os
import threading

from urllib.parse import unquote

from flask import Flask, redirect, request, jsonify

from backend.messaging import chat_store, sender
from backend.messaging.events import InboundMessage, StatusEvent, ReactionEvent, TypingEvent, parse_webhook_event
from backend.messaging.verify import verify_webhook_signature

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set by main.py before starting the server
_agent_handler = None
_main_loop: asyncio.AbstractEventLoop | None = None


def set_agent_handler(handler):
    """Register the async function that processes a message and returns a reply.

    Signature: async (text: str, from_number: str) -> str
    """
    global _agent_handler
    _agent_handler = handler


def set_main_loop(loop: asyncio.AbstractEventLoop):
    """Set the main asyncio event loop for coroutine submission from Flask threads."""
    global _main_loop
    _main_loop = loop


# ---------------------------------------------------------------------------
# BuckeyeMail OAuth routes
# ---------------------------------------------------------------------------

@app.route("/auth/buckeyemail/start")
def buckeyemail_start():
    """Redirect the user to the Microsoft OAuth login page."""
    from backend.integrations.buckeyemail.auth import build_auth_url

    phone = request.args.get("phone", "")
    if not phone:
        return "Missing phone parameter.", 400
    auth_url = build_auth_url(phone)
    return redirect(auth_url)


@app.route("/auth/buckeyemail/callback")
def buckeyemail_callback():
    """Handle the OAuth callback from Microsoft and store tokens."""
    from backend.integrations.buckeyemail.auth import exchange_code_for_tokens

    code = request.args.get("code")
    state = request.args.get("state", "")
    phone = unquote(state)

    if not code or not phone:
        return "Authorization failed — missing code or state.", 400

    result = exchange_code_for_tokens(code, phone)
    if "error" in result:
        logger.error("BuckeyeMail token exchange failed: %s", result)
        return "Authorization failed. Please try again.", 500

    return (
        "<html><body style='font-family:system-ui;text-align:center;padding:80px'>"
        "<h2>BuckeyeMail connected!</h2>"
        "<p>You can close this tab and go back to texting.</p>"
        "</body></html>"
    )


# ---------------------------------------------------------------------------
# Linq webhook
# ---------------------------------------------------------------------------

@app.route("/webhook", methods=["POST", "GET"])
def linq_webhook():
    # GET = health check
    if request.method == "GET":
        return "OK", 200

    raw_body = request.get_data(as_text=True)

    # Verify HMAC signature
    webhook_secret = os.environ.get("LINQ_WEBHOOK_SECRET", "")
    if webhook_secret:
        signature = request.headers.get("X-Webhook-Signature")
        timestamp = request.headers.get("X-Webhook-Timestamp")
        valid, reason = verify_webhook_signature(raw_body, signature, timestamp, webhook_secret)
        if not valid:
            logger.warning("Webhook signature rejected: %s", reason)
            return jsonify({"error": "Unauthorized", "reason": reason}), 401

    # Parse payload
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    # Return 200 immediately — process in background
    event = parse_webhook_event(payload)
    if event is not None:
        thread = threading.Thread(target=_process_event, args=(event,), daemon=True)
        thread.start()

    return jsonify({"status": "ok"}), 200


def _process_event(event):
    """Submit event processing to the main asyncio loop."""
    if _main_loop is None or _main_loop.is_closed():
        # Fallback: create a one-off loop if main loop isn't set yet
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_process_event_async(event))
        except Exception:
            logger.exception("Error processing webhook event")
        finally:
            loop.close()
        return

    future = asyncio.run_coroutine_threadsafe(_process_event_async(event), _main_loop)
    try:
        future.result(timeout=120)
    except Exception:
        logger.exception("Error processing webhook event")


async def _process_event_async(event):
    """Async event processing dispatched by type."""
    if isinstance(event, InboundMessage):
        await _handle_inbound_message(event)
    elif isinstance(event, StatusEvent):
        logger.info("Message %s status: %s", event.message_id, event.status)
    elif isinstance(event, ReactionEvent):
        action = "added" if event.added else "removed"
        logger.info("Reaction %s %s by %s on %s", event.reaction, action, event.from_number, event.message_id)
    elif isinstance(event, TypingEvent):
        state = "started" if event.started else "stopped"
        logger.info("Typing %s by %s", state, event.from_number)


def _is_registered_number(phone: str) -> bool:
    """Check Supabase profiles table to see if this phone number is registered."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_API_KEY", "")
    if not supabase_url or not supabase_key:
        logger.warning("Supabase env vars not set — allowing all numbers through")
        return True

    try:
        from auth import get_user, get_client
        return get_user(get_client(), phone) is not None
    except Exception:
        logger.exception("Supabase lookup failed for %s — allowing through", phone)
        return True


async def _handle_inbound_message(msg: InboundMessage):
    """Full alive-features message handling pipeline."""
    from_number = msg.from_number

    # Cache the chat mapping for outbound replies
    chat_store.set_chat_id(from_number, msg.chat_id)

    # ALIVE: Send read receipt
    await sender.mark_read(from_number)

    # Gate: only registered numbers get agent access
    if not _is_registered_number(from_number):
        logger.info("Unregistered number %s — sending signup prompt", from_number)
        await sender.send_message(
            from_number,
            "Hey! looks like you've discovered BuckeyeClaw. "
            "Head to buckeyeclaw.vercel.app to register.",
        )
        return

    # ALIVE: Acknowledge with a tapback
    await sender.react_to_message(msg.message_id, "like")

    # ALIVE: Start typing indicator
    await sender.start_typing(from_number)

    if not msg.text:
        await sender.stop_typing(from_number)
        return

    logger.info("Message from %s via %s: %s", from_number, msg.service, msg.text[:100])

    try:
        if _agent_handler:
            reply = await _agent_handler(msg.text, from_number)
        else:
            reply = "BuckeyeClaw is starting up, please try again in a moment."

        await sender.stop_typing(from_number)
        await sender.send_message(from_number, reply)

    except Exception:
        logger.exception("Agent error processing message from %s", from_number)
        await sender.stop_typing(from_number)
        await sender.send_message(from_number, "Sorry, something went wrong. Please try again.")
