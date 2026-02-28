"""Canvas (Carmen) REST API routes for the frontend dashboard.

Exposes /api/canvas/courses, /api/canvas/assignments, and /api/canvas/schedule
as JSON endpoints.  The Next.js frontend proxies /api/* to Flask on port 5000.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify

from canvasapi import Canvas

from auth.client import get_client

logger = logging.getLogger(__name__)

canvas_api = Blueprint("canvas_api", __name__)


def _get_canvas() -> Canvas:
    """Return a Canvas client using the token stored in Supabase user_integrations."""
    api_url = os.environ.get("CANVAS_API_URL", "https://osu.instructure.com")
    try:
        supabase = get_client()
        row = (
            supabase.table("user_integrations")
            .select("canvas_token")
            .not_.is_("canvas_token", "null")
            .limit(1)
            .maybe_single()
            .execute()
        )
        token = row.data.get("canvas_token") if row.data else None
    except Exception:
        logger.exception("Failed to fetch canvas token from Supabase")
        token = None

    if not token:
        raise RuntimeError("Canvas is not connected. Visit /app/connect to link your account.")
    return Canvas(api_url, token)


# ---------------------------------------------------------------------------
# GET /api/canvas/courses — active courses with current grades
# ---------------------------------------------------------------------------


@canvas_api.route("/api/canvas/courses")
def get_courses():
    try:
        canvas = _get_canvas()
        user = canvas.get_current_user()

        courses = list(user.get_courses(enrollment_state="active", include=["total_scores"]))
        enrollments = list(user.get_enrollments())

        # Map course_id -> grade info
        grade_map: dict[int, dict] = {}
        for e in enrollments:
            cid = getattr(e, "course_id", None)
            if cid is not None:
                grades = getattr(e, "grades", {})
                grade_map[cid] = {
                    "current_score": grades.get("current_score"),
                    "final_score": grades.get("final_score"),
                    "current_grade": grades.get("current_grade"),
                }

        result = []
        for c in courses:
            cid = c.id
            grades = grade_map.get(cid, {})
            score = grades.get("current_score") or grades.get("final_score")
            result.append({
                "id": cid,
                "name": getattr(c, "name", "Unknown"),
                "code": getattr(c, "course_code", ""),
                "percentage": round(float(score), 1) if score is not None else None,
                "letter": grades.get("current_grade") or "",
            })

        return jsonify(result)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.exception("Error fetching Canvas courses")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# GET /api/canvas/assignments — upcoming assignments with urgency
# ---------------------------------------------------------------------------

def _compute_urgency(due_dt: datetime, now: datetime) -> tuple[str, str]:
    """Return (dueLabel, urgency) for a given due datetime."""
    if due_dt < now:
        delta = now - due_dt
        hours = delta.total_seconds() / 3600
        if hours < 24:
            return f"overdue {int(hours)}h", "overdue"
        return f"overdue {int(hours / 24)}d", "overdue"

    delta = due_dt - now
    hours = delta.total_seconds() / 3600
    if hours <= 24:
        return "due tomorrow", "tomorrow"
    if hours <= 48:
        return f"due in 1d {int(hours % 24)}h", "soon"
    if hours <= 72:
        return f"due in 2d {int(hours % 24)}h", "soon"
    days = int(hours / 24)
    remaining_hours = int(hours % 24)
    if days < 7 and remaining_hours > 0:
        return f"due in {days}d {remaining_hours}h", "normal"
    return f"due in {days}d", "normal"


@canvas_api.route("/api/canvas/assignments")
def get_assignments():
    try:
        canvas = _get_canvas()
        user = canvas.get_current_user()
        courses = list(user.get_courses(enrollment_state="active"))

        now = datetime.now(timezone.utc)
        upcoming: list[dict] = []

        for course in courses:
            course_code = getattr(course, "course_code", getattr(course, "name", "Unknown"))
            try:
                assignments = course.get_assignments(
                    order_by="due_at",
                    bucket="upcoming",
                )
                for a in assignments:
                    due_str = getattr(a, "due_at", None)
                    if not due_str:
                        continue
                    due_dt = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                    due_label, urgency = _compute_urgency(due_dt, now)
                    upcoming.append({
                        "course": course_code,
                        "title": a.name,
                        "dueLabel": due_label,
                        "urgency": urgency,
                        "due_at": due_str,
                    })
            except Exception:
                logger.debug("Skipping assignments for %s", course_code, exc_info=True)
                continue

        # Sort: overdue first, then by due date
        urgency_order = {"overdue": 0, "tomorrow": 1, "soon": 2, "normal": 3}
        upcoming.sort(key=lambda x: (urgency_order.get(x["urgency"], 4), x.get("due_at", "")))

        # Drop the raw ISO string before sending to the client
        for item in upcoming:
            item.pop("due_at", None)

        return jsonify(upcoming[:25])
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.exception("Error fetching Canvas assignments")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# GET /api/canvas/schedule — weekly course schedule from Canvas calendar
# ---------------------------------------------------------------------------

_DAY_NAMES = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}


@canvas_api.route("/api/canvas/schedule")
def get_schedule():
    try:
        canvas = _get_canvas()
        user = canvas.get_current_user()
        courses = list(user.get_courses(enrollment_state="active"))

        if not courses:
            return jsonify([])

        # Build course_id -> course_code map
        code_map: dict[int, str] = {}
        context_codes: list[str] = []
        for c in courses:
            code_map[c.id] = getattr(c, "course_code", getattr(c, "name", ""))
            context_codes.append(f"course_{c.id}")

        # Query calendar events for the current term (last 30 days to next 30 days)
        start = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        end = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

        events = canvas.get_calendar_events(
            type="event",
            context_codes=context_codes,
            start_date=start,
            end_date=end,
            per_page=200,
        )

        # Aggregate events into unique course + time-slot blocks
        schedule: dict[str, dict] = {}

        for event in events:
            start_at = getattr(event, "start_at", None)
            end_at = getattr(event, "end_at", None)
            if not start_at or not end_at:
                continue

            start_dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_at.replace("Z", "+00:00"))

            weekday = start_dt.weekday()
            if weekday > 4:
                continue

            day_name = _DAY_NAMES[weekday]
            start_hour = round(start_dt.hour + start_dt.minute / 60, 2)
            end_hour = round(end_dt.hour + end_dt.minute / 60, 2)

            # Resolve course code from context_code
            ctx = getattr(event, "context_code", "")
            course_code = getattr(event, "title", "")
            if ctx.startswith("course_"):
                cid = int(ctx.split("_", 1)[1])
                course_code = code_map.get(cid, course_code)

            key = f"{course_code}|{start_hour}|{end_hour}"
            if key not in schedule:
                schedule[key] = {
                    "code": course_code,
                    "days": set(),
                    "startHour": start_hour,
                    "endHour": end_hour,
                }
            schedule[key]["days"].add(day_name)

        day_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        result = [
            {**s, "days": sorted(list(s["days"]), key=lambda d: day_order.index(d) if d in day_order else 5)}
            for s in schedule.values()
        ]

        return jsonify(result)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.exception("Error fetching Canvas schedule")
        return jsonify({"error": str(e)}), 500
