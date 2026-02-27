"""
Scheduled Grubhub order execution via APScheduler.

Jobs are persisted to a SQLite database so they survive server restarts.
When a scheduled order fires, the Appium automation runs and the user
is notified via Linq messaging.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / ".scheduled_orders.db"

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///{DB_PATH}"),
        }
        _scheduler = BackgroundScheduler(jobstores=jobstores)
    return _scheduler


def start():
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Grubhub order scheduler started (db: %s)", DB_PATH)


def shutdown():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Grubhub order scheduler shut down")


# ── Job execution ──────────────────────────────────────────────────────


def _execute_order(restaurant_name: str, items: str, from_number: str):
    """Run the Grubhub automation and notify the user. Runs in scheduler thread."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            _execute_order_async(restaurant_name, items, from_number)
        )
    finally:
        loop.close()


async def _execute_order_async(restaurant_name: str, items: str, from_number: str):
    from messaging import sender

    await sender.start_typing(from_number)
    try:
        from grubhub.automation import get_driver, intelligent_order

        driver = get_driver()
        result = intelligent_order(driver, restaurant_name, items)
        driver.quit()

        msg = f"Your scheduled order from {restaurant_name}:\n"
        if result["added"]:
            msg += f"Added: {', '.join(result['added'])}\n"
        if result["failed"]:
            msg += f"Could not add: {', '.join(result['failed'])}\n"
        msg += result["checkout_result"]

    except Exception as e:
        logger.exception("Scheduled order failed for %s", from_number)
        msg = (
            f"Your scheduled order from {restaurant_name} failed: "
            f"{type(e).__name__}. The emulator may not be running."
        )

    await sender.stop_typing(from_number)
    await sender.send_message(from_number, msg)


# ── Public API ─────────────────────────────────────────────────────────


def schedule_order(
    restaurant_name: str,
    items: str,
    run_at: datetime,
    from_number: str,
) -> str:
    """Schedule a Grubhub order. Returns the job ID."""
    sched = get_scheduler()
    job = sched.add_job(
        _execute_order,
        trigger="date",
        run_date=run_at,
        args=[restaurant_name, items, from_number],
        id=None,  # auto-generated
        replace_existing=False,
    )
    logger.info(
        "Scheduled order %s: %s from %s at %s for %s",
        job.id, items, restaurant_name, run_at, from_number,
    )
    return job.id


def get_scheduled_orders(from_number: str) -> list[dict]:
    """List pending scheduled orders for a phone number."""
    sched = get_scheduler()
    orders = []
    for job in sched.get_jobs():
        # job.args = [restaurant_name, items, from_number]
        if len(job.args) >= 3 and job.args[2] == from_number:
            orders.append({
                "job_id": job.id,
                "restaurant": job.args[0],
                "items": job.args[1],
                "scheduled_time": job.next_run_time.strftime("%I:%M %p on %b %d"),
            })
    return orders


def cancel_order(job_id: str) -> bool:
    """Cancel a scheduled order by job ID. Returns True if found and removed."""
    sched = get_scheduler()
    try:
        sched.remove_job(job_id)
        logger.info("Cancelled scheduled order %s", job_id)
        return True
    except Exception:
        return False


# ── Time parsing ───────────────────────────────────────────────────────


def parse_time(time_description: str) -> datetime:
    """Parse a natural-language time like '6pm', '6:30 PM', 'in 2 hours'.

    If the parsed time is in the past, assumes tomorrow.
    """
    text = time_description.strip().lower()
    now = datetime.now()

    # "in X hours/minutes"
    if text.startswith("in "):
        parts = text[3:].split()
        if len(parts) >= 2:
            try:
                amount = int(parts[0])
            except ValueError:
                amount = float(parts[0])
            unit = parts[1]
            if unit.startswith("hour"):
                return now + timedelta(hours=amount)
            elif unit.startswith("min"):
                return now + timedelta(minutes=amount)

    # Strip "at " prefix
    if text.startswith("at "):
        text = text[3:].strip()

    # Try common formats: "6pm", "6:30pm", "6:30 pm", "18:00"
    for fmt in ("%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
            target = now.replace(
                hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0,
            )
            if target <= now:
                target += timedelta(days=1)
            return target
        except ValueError:
            continue

    raise ValueError(f"Could not parse time: {time_description!r}")
