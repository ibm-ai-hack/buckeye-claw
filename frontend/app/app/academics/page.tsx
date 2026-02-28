"use client";

import { useEffect, useState } from "react";
import DomainHero from "@/components/DomainHero";
import GradeBar from "@/components/domain/GradeBar";
import ScheduleGrid from "@/components/domain/ScheduleGrid";
import AssignmentRow from "@/components/domain/AssignmentRow";

interface Course {
  id: number;
  name: string;
  code: string;
  percentage: number | null;
  letter: string;
}

interface Assignment {
  course: string;
  title: string;
  dueLabel: string;
  urgency: "normal" | "soon" | "tomorrow" | "overdue";
}

interface ScheduleBlock {
  code: string;
  days: string[];
  startHour: number;
  endHour: number;
}

const TABS = ["schedule", "grades", "assignments"] as const;
type Tab = (typeof TABS)[number];

export default function AcademicsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("schedule");

  const [courses, setCourses] = useState<Course[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [schedule, setSchedule] = useState<ScheduleBlock[]>([]);

  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingAssignments, setLoadingAssignments] = useState(true);
  const [loadingSchedule, setLoadingSchedule] = useState(true);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch all three in parallel
    fetch("/api/canvas/courses")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setCourses(data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoadingCourses(false));

    fetch("/api/canvas/assignments")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setAssignments(data);
      })
      .catch(() => {})
      .finally(() => setLoadingAssignments(false));

    fetch("/api/canvas/schedule")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setSchedule(data);
      })
      .catch(() => {})
      .finally(() => setLoadingSchedule(false));
  }, []);

  const isLoading =
    (activeTab === "grades" && loadingCourses) ||
    (activeTab === "assignments" && loadingAssignments) ||
    (activeTab === "schedule" && loadingSchedule);

  // Filter courses that have grade data
  const gradedCourses = courses.filter(
    (c) => c.percentage !== null && c.percentage !== undefined,
  );

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <DomainHero title="academics" accentColor="rgb(220,170,50)" />

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: 4,
          borderBottom: "1px solid rgba(255, 240, 220, 0.06)",
          padding: "0 32px",
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              fontFamily: "var(--font-jakarta)",
              fontWeight: activeTab === tab ? 500 : 400,
              fontSize: 15,
              color: activeTab === tab ? "#ede8e3" : "rgba(237, 232, 227, 0.45)",
              padding: "14px 20px",
              background: activeTab === tab ? "rgba(255, 240, 220, 0.05)" : "transparent",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid rgb(198, 50, 45)" : "2px solid transparent",
              borderRadius: "8px 8px 0 0",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 32px",
        }}
      >
        {/* Error banner */}
        {error && (
          <div
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 13,
              color: "rgba(255,255,255,0.5)",
              padding: "12px 16px",
              background: "rgba(198,40,40,0.08)",
              border: "1px solid rgba(198,40,40,0.15)",
              borderRadius: 8,
              marginBottom: 16,
            }}
          >
            Could not connect to Canvas. Make sure your CANVAS_API_TOKEN is set in the backend.
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div
            style={{
              fontFamily: "var(--font-jakarta)",
              fontSize: 14,
              color: "rgba(255,255,255,0.35)",
              padding: "40px 0",
              textAlign: "center",
              letterSpacing: "0.5px",
            }}
          >
            loading from carmen...
          </div>
        )}

        {/* Schedule tab */}
        {activeTab === "schedule" && !isLoading && (
          <div>
            {schedule.length > 0 ? (
              <ScheduleGrid courses={schedule} />
            ) : (
              <EmptyState message="no calendar events found in carmen" />
            )}
          </div>
        )}

        {/* Grades tab */}
        {activeTab === "grades" && !isLoading && (
          <div>
            {gradedCourses.length > 0 ? (
              gradedCourses.map((g, i) => (
                <GradeBar
                  key={g.id}
                  course={g.code}
                  percentage={g.percentage!}
                  letter={g.letter}
                  delay={i * 80}
                />
              ))
            ) : (
              <EmptyState message={error ? "could not load grades" : "no grade data available yet"} />
            )}
          </div>
        )}

        {/* Assignments tab */}
        {activeTab === "assignments" && !isLoading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {assignments.length > 0 ? (
              assignments.map((a) => (
                <AssignmentRow
                  key={`${a.course}-${a.title}`}
                  course={a.course}
                  title={a.title}
                  dueLabel={a.dueLabel}
                  urgency={a.urgency}
                />
              ))
            ) : (
              <EmptyState message={error ? "could not load assignments" : "no upcoming assignments"} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div
      style={{
        fontFamily: "var(--font-jakarta)",
        fontWeight: 400,
        fontSize: 14,
        color: "rgba(255,255,255,0.3)",
        padding: "48px 0",
        textAlign: "center",
        letterSpacing: "0.5px",
      }}
    >
      {message}
    </div>
  );
}
