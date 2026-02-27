import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("buckeyebot")


def main():
    from agent import create_agent
    from messaging.webhook import app, set_agent_handler
    from messaging import chat_store

    chat_store.load()

    agent = create_agent()
    logger.info("BuckeyeBot agent initialized")

    async def handle_message(text: str, from_number: str) -> str:
        try:
            response = await agent.run(text)
            return response.last_message.text
        except Exception as e:
            logger.exception("Agent error")
            return f"Sorry, I ran into an error: {type(e).__name__}. Please try again."

    set_agent_handler(handle_message)

    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting BuckeyeBot on port %d", port)
    logger.info("Configure your Linq webhook to POST to: http://<your-host>:%d/webhook", port)

    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
