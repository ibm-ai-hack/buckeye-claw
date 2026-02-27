import asyncio
import json
import logging
import os
import threading

from flask import Flask, request, jsonify

from messaging import chat_store, sender
from messaging.events import InboundMessage, StatusEvent, ReactionEvent, TypingEvent, parse_webhook_event
from messaging.verify import verify_webhook_signature

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set by main.py before starting the server
_agent_handler = None


def set_agent_handler(handler):
    """Register the async function that processes a message and returns a reply.

    Signature: async (text: str, from_number: str) -> str
    """
    global _agent_handler
    _agent_handler = handler


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
    """Background processing of webhook events."""
    loop = asyncio.new_event_loop()
    try:
        if isinstance(event, InboundMessage):
            loop.run_until_complete(_handle_inbound_message(event))
        elif isinstance(event, StatusEvent):
            logger.info("Message %s status: %s", event.message_id, event.status)
        elif isinstance(event, ReactionEvent):
            action = "added" if event.added else "removed"
            logger.info("Reaction %s %s by %s on %s", event.reaction, action, event.from_number, event.message_id)
        elif isinstance(event, TypingEvent):
            state = "started" if event.started else "stopped"
            logger.info("Typing %s by %s", state, event.from_number)
    except Exception:
        logger.exception("Error processing webhook event")
    finally:
        loop.close()


async def _handle_inbound_message(msg: InboundMessage):
    """Full alive-features message handling pipeline."""
    from_number = msg.from_number

    # Cache the chat mapping for outbound replies
    chat_store.set_chat_id(from_number, msg.chat_id)

    # ALIVE: Send read receipt
    await sender.mark_read(from_number)

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
            reply = "BuckeyeBot is starting up, please try again in a moment."

        await sender.stop_typing(from_number)
        await sender.send_message(from_number, reply)

    except Exception:
        logger.exception("Agent error processing message from %s", from_number)
        await sender.stop_typing(from_number)
        await sender.send_message(from_number, "Sorry, something went wrong. Please try again.")
