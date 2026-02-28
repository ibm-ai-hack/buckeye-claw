import { NextResponse } from "next/server";
import { canvasFetch, getCanvasToken } from "../_lib";

const DAY_NAMES: Record<number, string> = { 0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri" };
const DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri"];

export async function GET() {
  const token = await getCanvasToken();
  if (!token) {
    return NextResponse.json(
      { error: "Canvas not connected. Visit /app/connect to link your account." },
      { status: 503 },
    );
  }

  // Fetch active courses
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
  if (!courses.length) return NextResponse.json([]);

  // Build code map and context_codes list
  const codeMap: Record<number, string> = {};
  const contextParams = courses
    .map((c) => {
      codeMap[c.id] = c.course_code ?? c.name ?? "";
      return `context_codes[]=${encodeURIComponent(`course_${c.id}`)}`;
    })
    .join("&");

  const now = new Date();
  const startDate = new Date(now);
  startDate.setDate(startDate.getDate() - 30);
  const endDate = new Date(now);
  endDate.setDate(endDate.getDate() + 30);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);

  const eventsRes = await canvasFetch(
    `/api/v1/calendar_events?type=event&${contextParams}&start_date=${fmt(startDate)}&end_date=${fmt(endDate)}&per_page=200`,
    token,
  );

  if (!eventsRes.ok) return NextResponse.json([]);

  const events: any[] = await eventsRes.json();

  // Aggregate events into unique course + time-slot blocks
  const schedule: Record<string, { code: string; days: Set<string>; startHour: number; endHour: number }> = {};

  for (const event of events) {
    const startAt = event.start_at;
    const endAt = event.end_at;
    if (!startAt || !endAt) continue;

    const startDt = new Date(startAt);
    const endDt = new Date(endAt);
    // getUTCDay: Sun=0, Mon=1, ..., Fri=5, Sat=6 → subtract 1 → Mon=0..Fri=4, Sun=-1, Sat=5
    const dayIndex = startDt.getUTCDay() - 1;
    if (dayIndex < 0 || dayIndex > 4) continue;

    const dayName = DAY_NAMES[dayIndex];
    const startHour = Math.round((startDt.getUTCHours() + startDt.getUTCMinutes() / 60) * 100) / 100;
    const endHour = Math.round((endDt.getUTCHours() + endDt.getUTCMinutes() / 60) * 100) / 100;

    // Resolve course code from context_code
    let courseCode = event.title ?? "";
    const ctx: string = event.context_code ?? "";
    if (ctx.startsWith("course_")) {
      const cid = parseInt(ctx.slice(7), 10);
      courseCode = codeMap[cid] ?? courseCode;
    }

    const key = `${courseCode}|${startHour}|${endHour}`;
    if (!schedule[key]) {
      schedule[key] = { code: courseCode, days: new Set(), startHour, endHour };
    }
    schedule[key].days.add(dayName);
  }

  const result = Object.values(schedule).map((s) => ({
    ...s,
    days: [...s.days].sort((a, b) => DAY_ORDER.indexOf(a) - DAY_ORDER.indexOf(b)),
  }));

  return NextResponse.json(result);
}
