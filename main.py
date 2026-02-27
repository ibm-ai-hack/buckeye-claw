import asyncio
import logging
import os
import threading

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("buckeyeclaw")


async def async_main():
    from messaging.webhook import app, set_agent_handler, set_main_loop
    from messaging import chat_store
    from agents import run_pipeline

    # Load persisted chat-ID mappings
    chat_store.load()

    # Register the orchestrator pipeline as the message handler
    async def handle_message(text: str, from_number: str) -> str:
        try:
            return await run_pipeline(text, from_number)
        except Exception as e:
            logger.exception("Pipeline error")
            return f"Sorry, I ran into an error: {type(e).__name__}. Please try again."

    set_agent_handler(handle_message)

    # Share the main asyncio loop with webhook threads
    set_main_loop(asyncio.get_running_loop())

    # Run Flask in a daemon thread
    port = int(os.environ.get("PORT", 5000))
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
        daemon=True,
    )
    flask_thread.start()

    logger.info("BuckeyeClaw started on port %d", port)
    logger.info("Configure your Linq webhook to POST to: http://<your-host>:%d/webhook", port)

    # Keep the asyncio loop alive
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
