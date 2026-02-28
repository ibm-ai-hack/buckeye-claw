import os
from datetime import datetime

from beeai_framework.tools import StringToolOutput, tool

from canvasapi import Canvas

_canvas: Canvas | None = None


def _get_canvas() -> Canvas:
    global _canvas
    if _canvas is None:
        api_url = os.environ.get("CANVAS_API_URL", "https://osu.instructure.com")
        api_token = os.environ["CANVAS_API_TOKEN"]
        _canvas = Canvas(api_url, api_token)
    return _canvas


@tool
async def get_canvas_courses() -> StringToolOutput:
    """Get all current Canvas (Carmen) courses for the student."""
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
    return StringToolOutput(f"Your courses:\n" + "\n".join(
        f"- {c['name']} ({c['code']}) [ID: {c['id']}]" for c in result
    ) if result else "No active courses found.")


@tool
async def get_course_assignments(course_id: int) -> StringToolOutput:
    """Get all assignments for a Canvas course. Use get_canvas_courses first to find course IDs."""
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
    lines = []
    for a in result[:20]:
        status = "submitted" if a["submitted"] else "pending"
        lines.append(f"- {a['name']} | Due: {a['due']} | Points: {a['points']} | {status}")
    return StringToolOutput(f"Assignments for course {course_id}:\n" + "\n".join(lines) if lines else "No assignments found.")


@tool
async def get_upcoming_assignments() -> StringToolOutput:
    """Get upcoming assignments across all Canvas courses, sorted by due date."""
    canvas = _get_canvas()
    user = canvas.get_current_user()
    courses = user.get_courses(enrollment_state="active")
    upcoming = []
    now = datetime.utcnow().isoformat() + "Z"
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
    lines = []
    for a in upcoming[:15]:
        lines.append(f"- [{a['course']}] {a['name']} | Due: {a['due']} | {a['points']} pts")
    return StringToolOutput("Upcoming assignments:\n" + "\n".join(lines) if lines else "No upcoming assignments found.")


@tool
async def get_course_grades(course_id: int) -> StringToolOutput:
    """Get the student's grades/enrollments for a specific Canvas course."""
    canvas = _get_canvas()
    user = canvas.get_current_user()
    enrollments = user.get_enrollments()
    for e in enrollments:
        if getattr(e, "course_id", None) == course_id:
            grades = getattr(e, "grades", {})
            current = grades.get("current_score", "N/A")
            final = grades.get("final_score", "N/A")
            letter = grades.get("current_grade", "N/A")
            course_name = getattr(e, "course_name", f"Course {course_id}")
            return StringToolOutput(
                f"Grades for {course_name}:\n"
                f"- Current Score: {current}%\n"
                f"- Final Score: {final}%\n"
                f"- Letter Grade: {letter}"
            )
    return StringToolOutput(f"No grade data found for course {course_id}.")


@tool
async def get_course_announcements(course_id: int) -> StringToolOutput:
    """Get recent announcements for a Canvas course."""
    canvas = _get_canvas()
    course = canvas.get_course(course_id)
    announcements = course.get_discussion_topics(only_announcements=True)
    lines = []
    for a in list(announcements)[:10]:
        title = getattr(a, "title", "Untitled")
        posted = getattr(a, "posted_at", "Unknown date")
        lines.append(f"- {title} (posted {posted})")
    return StringToolOutput(f"Announcements for course {course_id}:\n" + "\n".join(lines) if lines else "No announcements found.")


@tool
async def get_canvas_todos() -> StringToolOutput:
    """Get the student's Canvas to-do items (ungraded submissions, upcoming items)."""
    canvas = _get_canvas()
    user = canvas.get_current_user()
    todos = user.get_todo_items() if hasattr(user, "get_todo_items") else []
    lines = []
    for t in todos:
        assignment = getattr(t, "assignment", {})
        name = assignment.get("name", "Unknown") if isinstance(assignment, dict) else getattr(assignment, "name", "Unknown")
        course = getattr(t, "course_id", "")
        lines.append(f"- {name} (Course: {course})")
    return StringToolOutput("To-do items:\n" + "\n".join(lines) if lines else "No to-do items.")


@tool
async def get_course_syllabus(course_id: int) -> StringToolOutput:
    """Get the syllabus for a Canvas course."""
    canvas = _get_canvas()
    course = canvas.get_course(course_id, include=["syllabus_body"])
    syllabus = getattr(course, "syllabus_body", None)
    if syllabus:
        # Strip HTML tags for SMS readability
        import re
        text = re.sub(r"<[^>]+>", " ", syllabus)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 1400:
            text = text[:1400] + "... (truncated)"
        return StringToolOutput(f"Syllabus for course {course_id}:\n{text}")
    return StringToolOutput(f"No syllabus found for course {course_id}.")
