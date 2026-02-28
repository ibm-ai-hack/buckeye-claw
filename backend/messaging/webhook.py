import asyncio
import json
import logging
import os
import threading

from urllib.parse import quote, unquote

from flask import Flask, redirect, request, jsonify

from backend.messaging import chat_store, sender
from backend.messaging.events import InboundMessage, StatusEvent, ReactionEvent, TypingEvent, parse_webhook_event
from backend.messaging.verify import verify_webhook_signature

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Canvas dashboard API
from backend.integrations.canvas.api import canvas_api
app.register_blueprint(canvas_api)

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


@app.route("/auth/buckeyemail/go/<code_>")
def buckeyemail_short_link(code_):
    """Resolve a short auth link and redirect to the real OAuth start."""
    from backend.integrations.buckeyemail.token_store import consume_auth_link

    phone = consume_auth_link(code_)
    if not phone:
        return "This link has expired or already been used.", 410
    return redirect(f"/auth/buckeyemail/start?phone={quote(phone, safe='')}")


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

    # Send SMS confirmation in background
    thread = threading.Thread(
        target=_send_oauth_confirmation, args=(phone,), daemon=True
    )
    thread.start()

    return _render_callback_success_page()


@app.route("/api/buckeyemail/status")
def buckeyemail_status():
    """Check if a phone number has connected BuckeyeMail."""
    from backend.integrations.buckeyemail.auth import get_access_token

    phone = request.args.get("phone", "")
    if not phone:
        return jsonify({"error": "Missing phone parameter"}), 400
    token = get_access_token(phone)
    return jsonify({"connected": token is not None})


def _send_oauth_confirmation(phone: str):
    """Send SMS confirmation that BuckeyeMail is now connected."""
    msg = (
        "BuckeyeMail is connected! You can now text me to "
        "check your inbox, search emails, or get your unread count."
    )
    if _main_loop is None or _main_loop.is_closed():
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(sender.send_message(phone, msg))
        except Exception:
            logger.exception("Failed to send BuckeyeMail confirmation to %s", phone)
        finally:
            loop.close()
    else:
        future = asyncio.run_coroutine_threadsafe(
            sender.send_message(phone, msg), _main_loop
        )
        try:
            future.result(timeout=15)
        except Exception:
            logger.exception("Failed to send BuckeyeMail confirmation to %s", phone)


def _render_callback_success_page() -> str:
    """Branded success page shown after BuckeyeMail OAuth completes."""
    return (
        '<!DOCTYPE html>'
        '<html lang="en"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>BuckeyeMail Connected</title>'
        '<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@200;300&family=Space+Mono&display=swap" rel="stylesheet">'
        '<style>'
        '*{margin:0;padding:0;box-sizing:border-box}'
        'body{min-height:100vh;background:#0a0a0a;display:flex;align-items:center;justify-content:center;font-family:"Space Mono",monospace}'
        '.card{text-align:center;padding:64px 48px;border-radius:20px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);max-width:440px}'
        '.check{width:56px;height:56px;border-radius:50%;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);display:inline-flex;align-items:center;justify-content:center;font-size:24px;color:#22c55e;margin-bottom:24px}'
        'h1{font-family:"Outfit",sans-serif;font-weight:200;font-size:28px;letter-spacing:0.15em;text-transform:lowercase;color:rgba(255,255,255,0.85);margin-bottom:12px}'
        'p{font-size:13px;color:rgba(255,255,255,0.4);line-height:1.7;letter-spacing:0.5px}'
        '.hint{margin-top:32px;font-size:11px;color:rgba(255,255,255,0.2);letter-spacing:1px}'
        '</style></head><body>'
        '<div class="card">'
        '<div class="check">&#10003;</div>'
        '<h1>buckeyemail connected</h1>'
        '<p>your osu email is linked. head back to your texts<br>and say "check my email" anytime.</p>'
        '<p class="hint">you can close this tab now</p>'
        '</div></body></html>'
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


async def _persist_last_reply(phone: str, reply: str) -> None:
    """Fire-and-forget: write the agent's last reply to Supabase for follow-up detection."""
    try:
        from auth import get_client
        supabase = get_client()
        supabase.table("profiles").update({"last_reply": reply}).eq("phone", phone).execute()
    except Exception:
        logger.warning("Failed to persist last_reply for %s", phone)


import re

_LAUGH_RE = re.compile(
    r"\b(lol|lmao|haha|rofl|dead|funny|joke|😂|🤣|💀)\b", re.IGNORECASE
)
_URGENT_RE = re.compile(
    r"\b(urgent|asap|emergency|help|important|!!|deadline|due)\b", re.IGNORECASE
)
_LOVE_RE = re.compile(
    r"\b(thank|thanks|thx|love|awesome|amazing|perfect|goat|🐐|❤️|🙏|appreciate)\b",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(r"\?\s*$")


def _pick_reaction(text: str) -> str:
    """Choose a tapback reaction based on the message content."""
    if not text:
        return "like"
    if _LAUGH_RE.search(text):
        return "laugh"
    if _LOVE_RE.search(text):
        return "love"
    if _URGENT_RE.search(text):
        return "emphasize"
    if _QUESTION_RE.search(text):
        return "like"
    return "like"


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

    # ALIVE: Acknowledge with a context-aware tapback
    await sender.react_to_message(msg.message_id, _pick_reaction(msg.text))

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
        asyncio.ensure_future(_persist_last_reply(from_number, reply))

    except Exception:
        logger.exception("Agent error processing message from %s", from_number)
        await sender.stop_typing(from_number)
        await sender.send_message(from_number, "Sorry, something went wrong. Please try again.")
