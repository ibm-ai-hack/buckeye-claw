import { NextResponse } from "next/server";
import { canvasFetch, computeUrgency, getCanvasToken, URGENCY_ORDER } from "../_lib";

export async function GET() {
  const token = await getCanvasToken();
  if (!token) {
    return NextResponse.json(
      { error: "Canvas not connected. Visit /app/connect to link your account." },
      { status: 503 },
    );
  }

  // Fetch active courses first
  const coursesRes = await canvasFetch(
    "/api/v1/courses?enrollment_state=active&per_page=100",
    token,
  );
  if (!coursesRes.ok) {
    return NextResponse.json(
      { error: `Canvas API error: ${coursesRes.status}` },
      { status: coursesRes.status },
    );
  }
  const courses: any[] = await coursesRes.json();

  const now = Date.now();

  // Fetch upcoming assignments for each course in parallel
  const perCourse = await Promise.all(
    courses.map(async (course) => {
      const code = course.course_code ?? course.name ?? "Unknown";
      try {
        const res = await canvasFetch(
          `/api/v1/courses/${course.id}/assignments?order_by=due_at&bucket=upcoming&per_page=100`,
          token,
        );
        if (!res.ok) return [];
        const assignments: any[] = await res.json();
        return assignments
          .filter((a) => a.due_at)
          .map((a) => {
            const dueMs = new Date(a.due_at).getTime();
            const { dueLabel, urgency } = computeUrgency(dueMs, now);
            return {
              course: code,
              title: a.name,
              dueLabel,
              urgency,
              _dueAt: a.due_at,
            };
          });
      } catch {
        return [];
      }
    }),
  );

  const upcoming = perCourse
    .flat()
    .sort(
      (a, b) =>
        (URGENCY_ORDER[a.urgency] ?? 4) - (URGENCY_ORDER[b.urgency] ?? 4) ||
        a._dueAt.localeCompare(b._dueAt),
    )
    .slice(0, 25)
    .map(({ _dueAt: _removed, ...rest }) => rest);

  return NextResponse.json(upcoming);
}
