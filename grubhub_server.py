"""
Entry point for the local Grubhub server.

Run on a machine with Android emulator + Appium, then tunnel via ngrok:

    python grubhub_server.py
    ngrok http 8000
"""

import logging
import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("grubhub-server")


def main():
    from backend.integrations.grubhub.scheduler import start as start_scheduler
    from backend.integrations.grubhub.server import app  # noqa: F401

    # Resume any persisted scheduled orders
    start_scheduler()

    port = int(os.environ.get("GRUBHUB_SERVER_PORT", 8000))
    logger.info("Starting Grubhub server on port %d", port)
    logger.info("Tunnel with: ngrok http %d", port)

    uvicorn.run(
        "backend.integrations.grubhub.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
