import asyncio
import os
import re
from contextvars import ContextVar
from datetime import datetime, timezone

from beeai_framework.tools import StringToolOutput, tool

from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken

# Per-request canvas token — set by the orchestrator before running canvas tools
_canvas_token_var: ContextVar[str] = ContextVar("canvas_token", default="")

_TOKEN_EXPIRED_MSG = (
    "Your Canvas access token has expired. Go to buckeyeclaw.vercel.app/app/connect, "
    "disconnect Canvas, then generate a new token at osu.instructure.com (Account → "
    "Settings → New Access Token) and reconnect."
)


def _get_canvas() -> Canvas:
    api_url = os.environ.get("CANVAS_API_URL", "https://osu.instructure.com")
    token = _canvas_token_var.get() or os.environ.get("CANVAS_API_TOKEN", "")
    return Canvas(api_url, token)


async def _run(fn):
    """Run a blocking Canvas function in a thread, catching auth errors cleanly."""
    try:
        return await asyncio.to_thread(fn)
    except InvalidAccessToken:
        raise RuntimeError(_TOKEN_EXPIRED_MSG)


@tool
async def get_canvas_courses() -> StringToolOutput:
    """Get all current Canvas (Carmen) courses for the student."""
    def _sync():
        canvas = _get_canvas()
        user = canvas.get_current_user()
        courses = user.get_courses(enrollment_state="active")
        result = []
        for c in courses:
            result.append({
                "id": c.id,
                "name": getattr(c, "name", "Unknown"),
                "code": getattr(c, "course_code", ""),
            })
        return result

    result = await _run(_sync)
    return StringToolOutput("Your courses:\n" + "\n".join(
        f"- {c['name']} ({c['code']}) [ID: {c['id']}]" for c in result
    ) if result else "No active courses found.")


@tool
async def get_course_assignments(course_id: int) -> StringToolOutput:
    """Get all assignments for a Canvas course. Use get_canvas_courses first to find course IDs."""
    def _sync():
        canvas = _get_canvas()
        course = canvas.get_course(course_id)
        assignments = course.get_assignments()
        result = []
        for a in assignments:
            result.append({
                "name": a.name,
                "due": str(getattr(a, "due_at", "No due date")),
                "points": getattr(a, "points_possible", "N/A"),
                "submitted": getattr(a, "has_submitted_submissions", False),
            })
        return result

    result = await _run(_sync)
    lines = []
    for a in result[:20]:
        status = "submitted" if a["submitted"] else "pending"
        lines.append(f"- {a['name']} | Due: {a['due']} | Points: {a['points']} | {status}")
    return StringToolOutput(f"Assignments for course {course_id}:\n" + "\n".join(lines) if lines else "No assignments found.")


@tool
async def get_upcoming_assignments() -> StringToolOutput:
    """Get upcoming assignments across all Canvas courses, sorted by due date."""
    now = datetime.now(timezone.utc).isoformat()

    def _sync():
        canvas = _get_canvas()
        user = canvas.get_current_user()
        courses = user.get_courses(enrollment_state="active")
        upcoming = []
        for course in courses:
            try:
                assignments = course.get_assignments(
                    order_by="due_at",
                    bucket="upcoming",
                )
                for a in assignments:
                    due = getattr(a, "due_at", None)
                    if due and due >= now:
                        upcoming.append({
                            "course": getattr(course, "name", "Unknown"),
                            "name": a.name,
                            "due": due,
                            "points": getattr(a, "points_possible", "N/A"),
                        })
            except Exception:
                continue
        upcoming.sort(key=lambda x: x["due"])
        return upcoming

    upcoming = await _run(_sync)
    lines = []
    for a in upcoming[:15]:
        lines.append(f"- [{a['course']}] {a['name']} | Due: {a['due']} | {a['points']} pts")
    return StringToolOutput("Upcoming assignments:\n" + "\n".join(lines) if lines else "No upcoming assignments found.")


@tool
async def get_course_grades(course_id: int) -> StringToolOutput:
    """Get the student's grades/enrollments for a specific Canvas course."""
    def _sync():
        canvas = _get_canvas()
        user = canvas.get_current_user()
        enrollments = user.get_enrollments()
        for e in enrollments:
            if getattr(e, "course_id", None) == course_id:
                grades = getattr(e, "grades", {})
                return {
                    "current": grades.get("current_score", "N/A"),
                    "final": grades.get("final_score", "N/A"),
                    "letter": grades.get("current_grade", "N/A"),
                    "course_name": getattr(e, "course_name", f"Course {course_id}"),
                }
        return None

    data = await _run(_sync)
    if data:
        return StringToolOutput(
            f"Grades for {data['course_name']}:\n"
            f"- Current Score: {data['current']}%\n"
            f"- Final Score: {data['final']}%\n"
            f"- Letter Grade: {data['letter']}"
        )
    return StringToolOutput(f"No grade data found for course {course_id}.")


@tool
async def get_course_announcements(course_id: int) -> StringToolOutput:
    """Get recent announcements for a Canvas course."""
    def _sync():
        canvas = _get_canvas()
        course = canvas.get_course(course_id)
        announcements = course.get_discussion_topics(only_announcements=True)
        lines = []
        for a in list(announcements)[:10]:
            title = getattr(a, "title", "Untitled")
            posted = getattr(a, "posted_at", "Unknown date")
            lines.append(f"- {title} (posted {posted})")
        return lines

    lines = await _run(_sync)
    return StringToolOutput(f"Announcements for course {course_id}:\n" + "\n".join(lines) if lines else "No announcements found.")


@tool
async def get_canvas_todos() -> StringToolOutput:
    """Get the student's Canvas to-do items (ungraded submissions, upcoming items)."""
    def _sync():
        canvas = _get_canvas()
        user = canvas.get_current_user()
        todos = user.get_todo_items() if hasattr(user, "get_todo_items") else []
        lines = []
        for t in todos:
            assignment = getattr(t, "assignment", {})
            name = assignment.get("name", "Unknown") if isinstance(assignment, dict) else getattr(assignment, "name", "Unknown")
            course = getattr(t, "course_id", "")
            lines.append(f"- {name} (Course: {course})")
        return lines

    lines = await _run(_sync)
    return StringToolOutput("To-do items:\n" + "\n".join(lines) if lines else "No to-do items.")


@tool
async def get_course_syllabus(course_id: int) -> StringToolOutput:
    """Get the syllabus for a Canvas course."""
    def _sync():
        canvas = _get_canvas()
        course = canvas.get_course(course_id, include=["syllabus_body"])
        syllabus = getattr(course, "syllabus_body", None)
        if syllabus:
            text = re.sub(r"<[^>]+>", " ", syllabus)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 1400:
                text = text[:1400] + "... (truncated)"
            return text
        return None

    text = await _run(_sync)
    if text:
        return StringToolOutput(f"Syllabus for course {course_id}:\n{text}")
    return StringToolOutput(f"No syllabus found for course {course_id}.")
