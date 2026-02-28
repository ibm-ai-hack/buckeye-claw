import { NextResponse } from "next/server";
import { canvasFetch, getCanvasToken } from "../_lib";

export async function GET() {
  const token = await getCanvasToken();
  if (!token) {
    return NextResponse.json(
      { error: "Canvas not connected. Visit /app/connect to link your account." },
      { status: 503 },
    );
  }

  const [coursesRes, enrollmentsRes] = await Promise.all([
    canvasFetch("/api/v1/courses?enrollment_state=active&include[]=total_scores&per_page=100", token),
    canvasFetch("/api/v1/users/self/enrollments?per_page=100", token),
  ]);

  if (!coursesRes.ok) {
    return NextResponse.json(
      { error: `Canvas API error: ${coursesRes.status}` },
      { status: coursesRes.status },
    );
  }

  const courses = await coursesRes.json();
  const enrollments: any[] = enrollmentsRes.ok ? await enrollmentsRes.json() : [];

  // Build course_id → grade info map
  const gradeMap: Record<number, { current_score: number | null; final_score: number | null; current_grade: string }> = {};
  for (const e of enrollments) {
    if (e.course_id != null && e.grades) {
      gradeMap[e.course_id] = {
        current_score: e.grades.current_score ?? null,
        final_score: e.grades.final_score ?? null,
        current_grade: e.grades.current_grade ?? "",
      };
    }
  }

  const result = courses.map((c: any) => {
    const grades = gradeMap[c.id] ?? {};
    const score = grades.current_score ?? grades.final_score ?? null;
    return {
      id: c.id,
      name: c.name ?? "Unknown",
      code: c.course_code ?? "",
      percentage: score !== null ? Math.round(score * 10) / 10 : null,
      letter: grades.current_grade ?? "",
    };
  });

  return NextResponse.json(result);
}
