"use client";

interface CourseBlock {
  code: string;
  days: string[];
  startHour: number;
  endHour: number;
  colorIndex?: number;
}

interface ScheduleGridProps {
  courses: CourseBlock[];
}

const DAYS = ["mon", "tue", "wed", "thu", "fri"];
const START_HOUR = 8;
const END_HOUR = 18;
const HOUR_HEIGHT = 48;
const OPACITIES = [0.25, 0.20, 0.15, 0.12, 0.10];

const DAY_MAP: Record<string, string> = {
  M: "mon", Mo: "mon", Mon: "mon", Monday: "mon",
  T: "tue", Tu: "tue", Tue: "tue", Tuesday: "tue",
  W: "wed", We: "wed", Wed: "wed", Wednesday: "wed",
  R: "thu", Th: "thu", Thu: "thu", Thursday: "thu",
  F: "fri", Fr: "fri", Fri: "fri", Friday: "fri",
};

function normalizeDays(days: string[]): string[] {
  return days.map((d) => DAY_MAP[d] || d.toLowerCase().slice(0, 3));
}

export default function ScheduleGrid({ courses }: ScheduleGridProps) {
  const totalHours = END_HOUR - START_HOUR;

  return (
    <div style={{ position: "relative" }}>
      {/* Day headers */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "48px repeat(5, 1fr)",
          gap: 0,
          marginBottom: 4,
        }}
      >
        <div />
        {DAYS.map((day) => (
          <div
            key={day}
            style={{
              fontFamily: "var(--font-space-mono)",
              fontWeight: 400,
              fontSize: 10,
              color: "rgba(255,255,255,0.25)",
              letterSpacing: "1px",
              textAlign: "center",
              padding: "4px 0",
            }}
          >
            {day}
          </div>
        ))}
      </div>

      {/* Grid body */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "48px repeat(5, 1fr)",
          position: "relative",
        }}
      >
        {/* Hour labels + grid lines */}
        {Array.from({ length: totalHours }, (_, i) => {
          const hour = START_HOUR + i;
          const label =
            hour === 12
              ? "12pm"
              : hour > 12
                ? `${hour - 12}pm`
                : `${hour}am`;
          return (
            <div
              key={hour}
              style={{
                gridColumn: "1 / -1",
                gridRow: i + 1,
                display: "grid",
                gridTemplateColumns: "48px repeat(5, 1fr)",
                height: HOUR_HEIGHT,
                borderTop: "1px solid rgba(255,255,255,0.02)",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-space-mono)",
                  fontWeight: 400,
                  fontSize: 9,
                  color: "rgba(255,255,255,0.15)",
                  paddingRight: 8,
                  textAlign: "right",
                  lineHeight: 1,
                }}
              >
                {label}
              </div>
            </div>
          );
        })}

        {/* Course blocks */}
        {courses.map((course, ci) => {
          const normalDays = normalizeDays(course.days);
          const opacity = OPACITIES[ci % OPACITIES.length];
          return normalDays.map((day) => {
            const dayIndex = DAYS.indexOf(day);
            if (dayIndex === -1) return null;

            const top = (course.startHour - START_HOUR) * HOUR_HEIGHT;
            const height = (course.endHour - course.startHour) * HOUR_HEIGHT;

            return (
              <div
                key={`${course.code}-${day}`}
                style={{
                  position: "absolute",
                  left: `calc(48px + ${dayIndex} * ((100% - 48px) / 5) + 2px)`,
                  width: `calc((100% - 48px) / 5 - 4px)`,
                  top: top + 28, // offset for header
                  height,
                  background: `rgba(198,40,40,${opacity})`,
                  border: "1px solid rgba(198,40,40,0.30)",
                  borderRadius: 6,
                  padding: "6px 8px",
                  display: "flex",
                  alignItems: "flex-start",
                  animation: `fadeInUp 200ms ease-out ${ci * 60}ms forwards`,
                  opacity: 0,
                  overflow: "hidden",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-space-mono)",
                    fontWeight: 400,
                    fontSize: 10,
                    color: "rgba(255,255,255,0.80)",
                    lineHeight: 1.3,
                  }}
                >
                  {course.code}
                </span>
              </div>
            );
          });
        })}
      </div>
    </div>
  );
}
