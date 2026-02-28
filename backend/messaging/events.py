from dataclasses import dataclass, field


@dataclass
class InboundMessage:
    message_id: str
    chat_id: str
    from_number: str
    to_number: str
    text: str
    attachments: list[dict] = field(default_factory=list)
    service: str = "SMS"
    sent_at: str = ""


@dataclass
class StatusEvent:
    message_id: str
    chat_id: str
    status: str  # "delivered" | "read" | "failed"


@dataclass
class ReactionEvent:
    message_id: str
    chat_id: str
    from_number: str
    reaction: str
    added: bool


@dataclass
class TypingEvent:
    chat_id: str
    from_number: str
    started: bool


def parse_webhook_event(
    payload: dict,
) -> InboundMessage | StatusEvent | ReactionEvent | TypingEvent | None:
    """Parse a Linq webhook event payload into a typed dataclass."""
    event_type = payload.get("event_type", "")
    data = payload.get("data", {})

    if event_type == "message.received":
        return _parse_inbound_message(data)
    elif event_type in ("message.delivered", "message.read", "message.failed"):
        status = event_type.split(".")[-1]
        return StatusEvent(
            message_id=data.get("id", ""),
            chat_id=data.get("chat", {}).get("id", ""),
            status=status,
        )
    elif event_type in ("reaction.added", "reaction.removed"):
        return ReactionEvent(
            message_id=data.get("message_id", data.get("id", "")),
            chat_id=data.get("chat", {}).get("id", ""),
            from_number=data.get("sender_handle", {}).get("handle", ""),
            reaction=data.get("reaction", data.get("type", "")),
            added=event_type == "reaction.added",
        )
    elif event_type in (
        "chat.typing_indicator.started",
        "chat.typing_indicator.stopped",
    ):
        return TypingEvent(
            chat_id=data.get("chat", {}).get("id", data.get("chat_id", "")),
            from_number=data.get("sender_handle", {}).get(
                "handle", data.get("handle", "")
            ),
            started=event_type.endswith("started"),
        )

    return None


def _parse_inbound_message(data: dict) -> InboundMessage:
    """Extract text and attachments from a message.received payload."""
    parts = data.get("parts", [])
    text_parts = []
    attachments = []

    for part in parts:
        ptype = part.get("type", "")
        if ptype == "text":
            text_parts.append(part.get("value", ""))
        elif ptype in ("media", "attachment"):
            attachments.append(
                {
                    "url": part.get("url", ""),
                    "mime_type": part.get("mime_type", ""),
                    "filename": part.get("filename", ""),
                }
            )

    chat = data.get("chat", {})
    sender = data.get("sender_handle", {})
    owner = chat.get("owner_handle", {})

    return InboundMessage(
        message_id=data.get("id", ""),
        chat_id=chat.get("id", ""),
        from_number=sender.get("handle", ""),
        to_number=owner.get("handle", ""),
        text="\n".join(text_parts),
        attachments=attachments,
        service=data.get("service", "SMS"),
        sent_at=data.get("sent_at", ""),
    )
