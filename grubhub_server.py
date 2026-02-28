"""
Entry point for the local Grubhub server.

Automatically starts the Android emulator, Appium, and Grubhub app,
then launches the FastAPI server. One command does everything:

    python grubhub_server.py

Optionally auto-starts ngrok if installed:

    python grubhub_server.py --ngrok
"""

import atexit
import logging
import os
import signal
import subprocess
import sys
import time

import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("grubhub-server")

# Track subprocesses so we can clean up on exit
_subprocesses: list[subprocess.Popen] = []


def _cleanup():
    for proc in _subprocesses:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


atexit.register(_cleanup)


# ── Emulator ──────────────────────────────────────────────────────────


def _ensure_emulator():
    """Start the Android emulator if it's not already running."""
    from backend.integrations.grubhub.emulator import is_emulator_running, list_avds

    if is_emulator_running():
        logger.info("Emulator already running")
        return

    avds = list_avds()
    if not avds:
        logger.error("No Android AVDs found. Create one in Android Studio first.")
        sys.exit(1)

    avd_name = avds[0]
    logger.info("Starting emulator: %s", avd_name)
    proc = subprocess.Popen(
        ["emulator", "-avd", avd_name, "-no-snapshot-save"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _subprocesses.append(proc)

    # Wait for boot (up to 120s)
    for i in range(60):
        try:
            result = subprocess.run(
                ["adb", "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip() == "1":
                logger.info("Emulator booted in ~%ds", i * 2)
                return
        except Exception:
            pass
        time.sleep(2)

    logger.error("Emulator failed to boot within 120s")
    sys.exit(1)


# ── Appium ────────────────────────────────────────────────────────────


def _is_appium_running() -> bool:
    import httpx
    try:
        resp = httpx.get("http://localhost:4723/status", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _ensure_appium():
    """Start Appium server if it's not already running."""
    if _is_appium_running():
        logger.info("Appium already running")
        return

    logger.info("Starting Appium server...")
    proc = subprocess.Popen(
        ["appium", "--relaxed-security"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _subprocesses.append(proc)

    # Wait for Appium to be ready (up to 30s)
    for i in range(15):
        time.sleep(2)
        if _is_appium_running():
            logger.info("Appium started in ~%ds", (i + 1) * 2)
            return

    logger.error("Appium failed to start within 30s")
    sys.exit(1)


# ── Grubhub app ──────────────────────────────────────────────────────


def _ensure_grubhub():
    """Launch the Grubhub app on the emulator."""
    from backend.integrations.grubhub.emulator import is_grubhub_installed, launch_grubhub

    if not is_grubhub_installed():
        logger.warning(
            "Grubhub is not installed on the emulator. "
            "Install it manually: adb install grubhub.apk"
        )
        return

    logger.info("Launching Grubhub app...")
    launch_grubhub()
    time.sleep(3)
    logger.info("Grubhub app launched")


# ── ngrok ─────────────────────────────────────────────────────────────


def _start_ngrok(port: int) -> str | None:
    """Start ngrok and return the public URL."""
    try:
        subprocess.run(["which", "ngrok"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("ngrok not found — skipping tunnel. Run 'ngrok http %d' manually.", port)
        return None

    logger.info("Starting ngrok tunnel...")
    proc = subprocess.Popen(
        ["ngrok", "http", str(port), "--log=stdout"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _subprocesses.append(proc)

    # Wait for ngrok to establish tunnel, then read URL from its API
    import httpx
    for i in range(10):
        time.sleep(2)
        try:
            resp = httpx.get("http://localhost:4040/api/tunnels", timeout=3)
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    url = t["public_url"]
                    logger.info("ngrok tunnel: %s", url)
                    return url
        except Exception:
            pass

    logger.warning("Could not read ngrok URL — check http://localhost:4040")
    return None


# ── Main ──────────────────────────────────────────────────────────────


def main():
    from backend.integrations.grubhub.scheduler import start as start_scheduler

    use_ngrok = "--ngrok" in sys.argv
    port = int(os.environ.get("GRUBHUB_SERVER_PORT", 8000))

    # Step 1: Boot emulator
    logger.info("=== Step 1/4: Emulator ===")
    _ensure_emulator()

    # Step 2: Start Appium
    logger.info("=== Step 2/4: Appium ===")
    _ensure_appium()

    # Step 3: Launch Grubhub app
    logger.info("=== Step 3/4: Grubhub app ===")
    _ensure_grubhub()

    # Step 4: Start ngrok (optional)
    ngrok_url = None
    if use_ngrok:
        logger.info("=== Step 4/4: ngrok ===")
        ngrok_url = _start_ngrok(port)
    else:
        logger.info("=== Step 4/4: Skipping ngrok (pass --ngrok to enable) ===")

    # Resume persisted scheduled orders
    start_scheduler()

    # Print summary
    logger.info("=" * 50)
    logger.info("Grubhub server ready on port %d", port)
    if ngrok_url:
        logger.info("")
        logger.info("Set these in your cloud deployment:")
        logger.info("  GRUBHUB_SERVER_URL=%s", ngrok_url)
        logger.info("  GRUBHUB_SERVER_KEY=%s", os.environ.get("GRUBHUB_SERVER_KEY", "(not set!)"))
    else:
        logger.info("Run with --ngrok or manually: ngrok http %d", port)
    logger.info("=" * 50)

    uvicorn.run(
        "backend.integrations.grubhub.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
