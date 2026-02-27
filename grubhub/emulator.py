import logging
import subprocess
import time

logger = logging.getLogger(__name__)

GRUBHUB_PACKAGE = "com.grubhub.android"


def list_avds() -> list[str]:
    result = subprocess.run(
        ["emulator", "-list-avds"],
        capture_output=True, text=True, timeout=10,
    )
    return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]


def start_emulator(avd_name: str | None = None) -> str:
    if avd_name is None:
        avds = list_avds()
        if not avds:
            raise RuntimeError("No Android AVDs found. Create one in Android Studio first.")
        avd_name = avds[0]

    logger.info("Starting emulator: %s", avd_name)
    subprocess.Popen(
        ["emulator", "-avd", avd_name, "-no-snapshot-save"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # Wait for device to boot
    for _ in range(60):
        result = subprocess.run(
            ["adb", "shell", "getprop", "sys.boot_completed"],
            capture_output=True, text=True, timeout=5,
        )
        if result.stdout.strip() == "1":
            logger.info("Emulator booted successfully")
            return avd_name
        time.sleep(2)

    raise RuntimeError(f"Emulator {avd_name} failed to boot within 120 seconds")


def is_emulator_running() -> bool:
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True, text=True, timeout=5,
    )
    return "emulator" in result.stdout


def is_grubhub_installed() -> bool:
    result = subprocess.run(
        ["adb", "shell", "pm", "list", "packages", GRUBHUB_PACKAGE],
        capture_output=True, text=True, timeout=10,
    )
    return GRUBHUB_PACKAGE in result.stdout


def install_grubhub(apk_path: str) -> None:
    logger.info("Installing Grubhub APK: %s", apk_path)
    subprocess.run(
        ["adb", "install", apk_path],
        check=True, timeout=60,
    )


def launch_grubhub() -> None:
    subprocess.run(
        ["adb", "shell", "am", "start", "-n",
         f"{GRUBHUB_PACKAGE}/{GRUBHUB_PACKAGE}.ui.LaunchActivity"],
        check=True, timeout=10,
    )
